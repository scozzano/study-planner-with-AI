from typing import List, Optional

from pydantic import BaseModel

from src.model.records.university_subject_record import UniversitySubjectRecord


class UniversityRecord(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    degree: Optional[str] = None
    plan: str
    subjects: List[UniversitySubjectRecord]
