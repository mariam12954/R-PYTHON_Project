from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class DepartmentEnum(str, Enum):
    CS         = "CS"
    IT         = "IT"
    AI         = "AI"
    IS         = "IS"
    Robotics   = "Robotics"
    Multimedia = "Multimedia"

class StudentCreate(BaseModel):
    full_name:  str
    department: DepartmentEnum
    gpa:        float = Field(ge=0.0, le=4.0)
    year:       int   = Field(ge=1, le=6)
    phone:      Optional[str] = None
    address:    Optional[str] = None
    user_id:    int

class StudentUpdate(BaseModel):
    full_name:  Optional[str]            = None
    department: Optional[DepartmentEnum] = None
    gpa:        Optional[float]          = Field(default=None, ge=0.0, le=4.0)
    year:       Optional[int]            = Field(default=None, ge=1, le=6)
    phone:      Optional[str]            = None
    address:    Optional[str]            = None

class StudentOut(BaseModel):
    id:         int
    user_id:    int
    full_name:  str
    department: str
    gpa:        float
    year:       int
    phone:      Optional[str]
    address:    Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True