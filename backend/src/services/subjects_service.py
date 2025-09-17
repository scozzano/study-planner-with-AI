from typing import List

from src.model.records.degree_subject_information_record import DegreeSubjectInformationRecord
from src.model.records.subject_record import SubjectRecord
from src.repository.subjects_repository import DynamoSubjectsRepository


class SubjectsService():
    def __init__(self, repository: DynamoSubjectsRepository):
        self.repository = repository

    def get_subjects(self) -> List[SubjectRecord]:
        return self.repository.get_subjects()

    def get_subject_details(self, degree_id: str, subject_id: str) -> DegreeSubjectInformationRecord:
        subject = self.repository.get_subject(degree_id, subject_id)
        requiredSubjects = self.repository.get_subject_requirement(degree_id, subject_id)
        return DegreeSubjectInformationRecord(subject=subject, requirements=requiredSubjects)
