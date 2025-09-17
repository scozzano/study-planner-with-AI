from typing import Optional

from pydantic import BaseModel


class StudentSubjectRecord(BaseModel):
    code: str
    name: Optional[str] = None
    semester: Optional[str] = None
    date: Optional[str] = None
    status: Optional[str] = None
    grade: Optional[int] = None
    attempts: Optional[int] = None
    last_attempt_date: Optional[str] = None
    result_type: Optional[str] = None
    result_source: Optional[str] = None
