from typing import List

import boto3

from src.model.records.student_record import StudentRecord
from src.model.records.student_subject_record import StudentSubjectRecord


class DynamoStudentsRepository():
    def __init__(self):
        dynamodb = boto3.resource("dynamodb")
        self.table = dynamodb.Table("AdaProjectTable")

    def save_schooling(self, student_record: StudentRecord) -> None:
        record_dict = student_record.dict()

        item = {
            "PK": f"DEGREE#{student_record.degreeId}",
            "SK": f"STUDENTS#{student_record.id}",
            **record_dict
        }
        self.table.put_item(Item=item)

        plan_key = {
            "PK": f"DEGREE#{student_record.degreeId}",
            "SK": f"STUDENT-PLAN#{student_record.id}"
        }

        response = self.table.get_item(Key=plan_key)
        existing_item = response.get("Item")

        if existing_item:
            existing_record = StudentRecord(**existing_item)
            updated = False

            for new_subject in student_record.subjects:
                for i, existing_subject in enumerate(existing_record.subjects):
                    if existing_subject.code == new_subject.code:
                        has_changes = (
                            existing_subject.status != new_subject.status or
                            existing_subject.grade != new_subject.grade or
                            existing_subject.semester != new_subject.semester
                        )
                        if has_changes:
                            existing_record.subjects[i] = new_subject
                            updated = True
                        break

            if updated:
                self.add_student_plan(existing_record)
        else:
            self.add_student_plan(student_record)

    def get_schooling(self, degree_id: str, student_id: str) -> StudentRecord:
        response = self.table.get_item(
            Key={
            "PK": f"DEGREE#{degree_id}",
            "SK": f"STUDENTS#{student_id}",
            }
        )
        item = response.get("Item")
        if not item:
            raise ValueError(f"El estudiante: {student_id} no fue encontrado")

        return StudentRecord(**item)

    def get_student_plan(self, degree_id: str, student_id: str) -> StudentRecord:
        response = self.table.get_item(
            Key={
            "PK": f"DEGREE#{degree_id}",
            "SK": f"STUDENT-PLAN#{student_id}"
            }
        )
        item = response.get("Item")
        if not item:
            raise ValueError(f"El estudiante: {student_id} no fue encontrado")

        return StudentRecord(**item)

    def add_student_plan(self, student_record: StudentRecord) -> None:
        record_dict = student_record.dict()
        item = {
            "PK": f"DEGREE#{student_record.degreeId}",
            "SK": f"STUDENT-PLAN#{student_record.id}",
            **record_dict
        }
        self.table.put_item(Item=item)

    def edit_student_plan(self, degree_id: str, student_id: str,
                          subjects: List[StudentSubjectRecord]) -> None:
        response = self.table.get_item(
            Key={
            "PK": f"DEGREE#{degree_id}",
            "SK": f"STUDENT-PLAN#{student_id}",
            }
        )
        item = response.get("Item")
        if not item:
            raise ValueError(f"El estudiante: {student_id} no fue encontrado")

        new_student_record = StudentRecord(**item)
        updated_any = False

        for subject in subjects:
            for i, subj in enumerate(new_student_record.subjects):
                if subj.code == subject.code:
                    if subj.status.strip().lower() != "apr":
                        print(f"Actualizando materia {subject.code} para el estudiante {student_id}")
                        if subject.status is not None:
                            new_student_record.subjects[i].status = subject.status
                        if subject.grade is not None:
                            new_student_record.subjects[i].grade = subject.grade
                        if subject.semester is not None:
                            new_student_record.subjects[i].semester = subject.semester
                        updated_any = True
                    break

        if not updated_any:
            raise ValueError(
                f"Ninguna materia fue actualizada para el estudiante: {student_id}. "
                "Puede que todas estén aprobadas o no existan."
            )

        record_dict = new_student_record.dict()
        item = {
            "PK": f"DEGREE#{degree_id}",
            "SK": f"STUDENT-PLAN#{new_student_record.id}",
            **record_dict
        }
        self.table.put_item(Item=item)

    def get_all_schooling(self) -> List[StudentRecord]:
        response = self.table.scan(
            FilterExpression="begins_with(PK, :pk) AND begins_with(SK, :sk)",
            ExpressionAttributeValues={
                ":pk": "DEGREE#",
                ":sk": "STUDENTS#"
            }
        )
        items = response.get("Items", [])
        return [StudentRecord(**item) for item in items]