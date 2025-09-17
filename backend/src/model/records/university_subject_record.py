from typing import List, Optional

from pydantic import BaseModel


class UniversitySubjectRecord(BaseModel):
    id: Optional[int] = None
    name: str
    semester: float
    subjectIds: Optional[List[int]] = None
