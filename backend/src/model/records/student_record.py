from typing import List, Optional

from pydantic import BaseModel

from src.model.records.student_subject_record import StudentSubjectRecord


class StudentRecord(BaseModel):
    id: str
    name: str
    document: str
    degreeId: str
    enrollment_number: str
    title: str
    plan: str
    start_date: str
    graduation_date: Optional[str]
    average_grade: Optional[int]
    average_approved_grade: Optional[int]
    subjects_required: int
    subjects_obtained: int
    failed_subjects: int
    subjects: List[StudentSubjectRecord]
