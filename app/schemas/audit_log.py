from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuditLogOut(BaseModel):
    id: int
    user_id: int
    action: str
    target_student_id: Optional[int]
    updated_fields: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True