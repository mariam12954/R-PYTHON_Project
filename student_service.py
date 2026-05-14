import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.cache import cache_get_json, cache_set_json, cache_delete, cache_delete_pattern
from app.core.config import settings
from app.models.user import User
from app.models.student import Student
from app.models.audit_log import AuditLog
from app.schemas.student import StudentCreate, StudentUpdate

logger = logging.getLogger("app.students")


def _student_to_dict(student: Student) -> Dict[str, Any]:
    return {
        "id": student.id,
        "user_id": student.user_id,
        "full_name": student.full_name,
        "department": student.department,
        "gpa": student.gpa,
        "year": student.year,
        "phone": student.phone,
        "address": student.address,
        "created_at": student.created_at.isoformat() if student.created_at else None,
        "updated_at": student.updated_at.isoformat() if student.updated_at else None,
    }


def _student_cache_key(student_id: int) -> str:
    return f"student:{student_id}"


def _student_user_cache_key(user_id: int) -> str:
    return f"student:user:{user_id}"


def _students_list_cache_key(
    department: Optional[str],
    search: Optional[str],
    min_gpa: Optional[float],
    max_gpa: Optional[float],
    skip: int,
    limit: int,
) -> str:
    return (
        "students:all:"
        f"dept={department or ''}:"
        f"search={search or ''}:"
        f"min={'' if min_gpa is None else min_gpa}:"
        f"max={'' if max_gpa is None else max_gpa}:"
        f"skip={skip}:limit={limit}"
    )


def _invalidate_student_cache(student_id: int, user_id: int) -> None:
    cache_delete(_student_cache_key(student_id))
    cache_delete(_student_user_cache_key(user_id))
    cache_delete_pattern("students:all:*")


def get_student_for_read(db: Session, student_id: int) -> Dict[str, Any]:
    cache_key = _student_cache_key(student_id)
    cached = cache_get_json(cache_key)
    if cached is not None:
        return cached

    student = get_student_by_id(db, student_id)
    data = _student_to_dict(student)
    cache_set_json(cache_key, data, settings.CACHE_TTL_SECONDS)
    return data


def get_student_by_user_id_cached(db: Session, user_id: int) -> Dict[str, Any]:
    cache_key = _student_user_cache_key(user_id)
    cached = cache_get_json(cache_key)
    if cached is not None:
        return cached

    student = get_student_by_user_id(db, user_id)
    data = _student_to_dict(student)
    cache_set_json(cache_key, data, settings.CACHE_TTL_SECONDS)
    return data


def get_all_students_cached(
    db: Session,
    department: Optional[str] = None,
    search: Optional[str] = None,
    min_gpa: Optional[float] = None,
    max_gpa: Optional[float] = None,
    skip: int = 0,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    cache_key = _students_list_cache_key(department, search, min_gpa, max_gpa, skip, limit)
    cached = cache_get_json(cache_key)
    if cached is not None:
        return cached

    students = get_all_students(db, department, search, min_gpa, max_gpa, skip, limit)
    data = [_student_to_dict(student) for student in students]
    cache_set_json(cache_key, data, settings.CACHE_TTL_SECONDS)
    return data

def create_student(db: Session, data: StudentCreate, created_by_user_id: int) -> Student:
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(Student).filter(Student.user_id == data.user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student profile already exists for this user")

    student = Student(**data.model_dump())
    db.add(student)
    db.flush()

    log = AuditLog(
        user_id=created_by_user_id,
        action="CREATE",
        target_student_id=student.id,
        updated_fields=json.dumps(data.model_dump())
    )
    db.add(log)
    db.commit()
    db.refresh(student)
    _invalidate_student_cache(student.id, student.user_id)
    cache_set_json(_student_cache_key(student.id), _student_to_dict(student), settings.CACHE_TTL_SECONDS)
    cache_set_json(_student_user_cache_key(student.user_id), _student_to_dict(student), settings.CACHE_TTL_SECONDS)
    logger.info("Student created student_id=%s user_id=%s", student.id, student.user_id)
    return student

def get_all_students(db: Session, department: str = None, search: str = None, min_gpa: float = None,
                     max_gpa: float = None, skip: int = 0, limit: int = 10):
    query = db.query(Student)
    if search:
        query = query.filter(Student.full_name.ilike(f"%{search}%"))
    if department:
        query = query.filter(Student.department.ilike(f"%{department}%"))
    if min_gpa is not None:
        query = query.filter(Student.gpa >= min_gpa)
    if max_gpa is not None:
        query = query.filter(Student.gpa <= max_gpa)
    return query.order_by(Student.created_at.desc()).offset(skip).limit(limit).all()

def get_student_by_id(db: Session, student_id: int) -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

def get_student_by_user_id(db: Session, user_id: int) -> Student:
    student = db.query(Student).filter(Student.user_id == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student

def update_student(db: Session, student_id: int, data: StudentUpdate, updated_by_user_id: int) -> Student:
    student = get_student_by_id(db, student_id)
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    for field, value in update_data.items():
        setattr(student, field, value)
    student.updated_at = datetime.utcnow()

    # Audit log
    log = AuditLog(
        user_id=updated_by_user_id,
        action="UPDATE",
        target_student_id=student_id,
        updated_fields=json.dumps(update_data)
    )
    db.add(log)
    db.commit()
    db.refresh(student)
    _invalidate_student_cache(student_id, student.user_id)
    cache_set_json(_student_cache_key(student.id), _student_to_dict(student), settings.CACHE_TTL_SECONDS)
    cache_set_json(_student_user_cache_key(student.user_id), _student_to_dict(student), settings.CACHE_TTL_SECONDS)
    logger.info("Student updated student_id=%s user_id=%s", student.id, student.user_id)
    return student

def delete_student(db: Session, student_id: int, deleted_by_user_id: int) -> dict:
    student = get_student_by_id(db, student_id)
    snapshot = {
        "full_name": student.full_name,
        "department": student.department,
        "gpa": student.gpa,
        "year": student.year,
        "phone": student.phone,
        "address": student.address,
        "user_id": student.user_id,
    }
    db.add(AuditLog(
        user_id=deleted_by_user_id,
        action="DELETE",
        target_student_id=student_id,
        updated_fields=json.dumps(snapshot)
    ))
    db.delete(student)
    db.commit()
    _invalidate_student_cache(student_id, student.user_id)
    logger.info("Student deleted student_id=%s user_id=%s", student_id, student.user_id)
    return {"message": f"Student {student_id} deleted successfully"}