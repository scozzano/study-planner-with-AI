from typing import List

from src.model.records.student_record import StudentRecord
from src.model.records.student_subject_record import StudentSubjectRecord
from src.repository.students_repository import DynamoStudentsRepository


class StudentService():
    def __init__(self, repository: DynamoStudentsRepository):
        self.repository = repository

    def save_schooling(self, student_record: StudentRecord) -> dict:
        self.repository.save_schooling(student_record)

    def upload_schooling(self, pdf_bytes: bytes) -> dict:
        from src.support.utils.pdf_processor import extract_schooling_data
        student_record = extract_schooling_data(pdf_bytes)
        self.save_schooling(student_record)
        return {"studentId": student_record.id,
                "degreeId": student_record.degreeId,
                "name": student_record.name}

    def get_schooling(self, degree_id: str, student_id: str) -> StudentRecord:
        return self.repository.get_schooling(degree_id, student_id)

    def get_student_plan(self, degree_id: str, student_id: str) -> StudentRecord:
        return self.repository.get_student_plan(degree_id, student_id)

    def edit_student_plan(self, degree_id: str, student_id: str, subjects: List[StudentSubjectRecord]) -> None:
        return self.repository.edit_student_plan(degree_id, student_id, subjects)
