from typing import List

import boto3
from boto3.dynamodb.conditions import Key

from src.model.records.requirements_record import RequirementsRecord
from src.model.records.subject_record import SubjectRecord

class DynamoSubjectsRepository():
    def __init__(self):
        dynamodb = boto3.resource("dynamodb")
        self.table = dynamodb.Table("AdaProjectTable")

    def get_subject(self, subject_id: str) -> SubjectRecord:
        response = self.table.get_item(
            Key={
                "PK": "SUBJECTS#",
                "SK": f"SUBJECTS#{subject_id}"
            }
        )

        item = response.get("Item")
        if not item:
            raise ValueError(f"Subject with id {subject_id} not found")

        sk = item.get("SK", "")
        name = item.get("name", "")
        extracted_id = sk.replace("SUBJECTS#", "")

        return SubjectRecord(id=extracted_id, name=name)

    def get_subjects(self) -> List[SubjectRecord]:
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq("SUBJECTS#") &
            Key("SK").begins_with("SUBJECTS#")
        )

        items = response.get("Items", [])

        subjects = []
        for item in items:
            sk = item.get("SK", "")
            subject_id = sk.replace("SUBJECTS#", "")
            name = item.get("name", "")

            subjects.append(SubjectRecord(id=subject_id, name=name))

        return subjects

    def get_subject_requirement(self, degree_id: str,
                                subject_id: str) -> RequirementsRecord:
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"DEGREE#{degree_id}") &
            Key("SK").eq(f"SUBJECTS#{subject_id}")
        )
        items = response.get("Items", [])
        if not items:
            return RequirementsRecord(
                subjectId=subject_id,
                parcialRequirements=[],
                totalRequirements=[],
                standing=0
            )
        return RequirementsRecord(**items[0])
