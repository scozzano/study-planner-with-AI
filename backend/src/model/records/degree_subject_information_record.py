from pydantic import BaseModel

from src.model.records.requirements_record import RequirementsRecord
from src.model.records.subject_record import SubjectRecord


class DegreeSubjectInformationRecord(BaseModel):
    subject: SubjectRecord
    requirements: RequirementsRecord
