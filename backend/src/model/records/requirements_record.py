from typing import List

from pydantic import BaseModel

from src.model.records.requirer_subject_record import RequirerSubjectRecord


class RequirementsRecord(BaseModel):
    subjectId: str
    name: str
    parcialRequirements: List[RequirerSubjectRecord]
    totalRequirements: List[RequirerSubjectRecord]
    standing: int
