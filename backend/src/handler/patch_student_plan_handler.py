import json
import logging

from src.model.records.student_subject_record import StudentSubjectRecord
from src.repository.students_repository import DynamoStudentsRepository
from src.services.student_service import StudentService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

students_repository = DynamoStudentsRepository()
student_service = StudentService(students_repository)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "OPTIONS,POST,PATCH"
}


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": ""
        }

    try:
        path_params = event.get("pathParameters") or {}
        student_id = path_params.get("student_id")

        if not student_id:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Falta el student_id en el path"})
            }

        if "body" not in event or not event["body"]:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Falta el cuerpo con las materias"})
            }

        body = json.loads(event["body"])
        subject_dicts = body.get("subjects", [])

        if not isinstance(subject_dicts, list) or not subject_dicts:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "El campo 'subjects' debe ser una lista no vacía"})
            }

        subjects = []
        for subj in subject_dicts:
            if "code" not in subj:
                return {
                    "statusCode": 400,
                    "headers": CORS_HEADERS,
                    "body": json.dumps({"error": "Cada materia debe tener al menos un 'code'"})
                }
            subjects.append(StudentSubjectRecord(**subj))

        student_service.edit_student_plan(student_id, subjects)

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": "Plan de estudiante actualizado correctamente"})
        }

    except ValueError as ve:
        logger.warning(f"Estudiante no encontrado: {str(ve)}")
        return {
            "statusCode": 404,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(ve)})
        }

    except Exception as e:
        logger.error(f"Error al editar el plan: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"{str(e)}"})
        }
