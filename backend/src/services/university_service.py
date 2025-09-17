from src.model.records.university_record import UniversityRecord
from src.repository.university_repository import DynamoUniversityRepository


class UniversityService():
    def __init__(self, repository: DynamoUniversityRepository):
        self.repository = repository

    def get_university_degree(self, degreeId: str) -> UniversityRecord:
        return self.repository.get_degree(degreeId)