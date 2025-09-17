import json
import logging

from src.repository.students_repository import DynamoStudentsRepository
from src.services.student_service import StudentService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

students_repository = DynamoStudentsRepository()
student_service = StudentService(students_repository)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
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
        degree_id = path_params.get("degree_id")

        if not student_id:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Falta el identificador del estudiante"})
            }

        if not degree_id:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Falta el identificador de la carrera"})
            }

        result = student_service.get_student_plan(degree_id,student_id)

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(result.dict())
        }

    except ValueError as ve:
        logger.warning(f"Estudiante no encontrado: {str(ve)}")
        return {
            "statusCode": 404,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(ve)})
        }

    except Exception as e:
        logger.error(f"Error al obtener el plan: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"{str(e)}"})
        }
