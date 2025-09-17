import json
import logging

from src.repository.subjects_repository import DynamoSubjectsRepository
from src.services.subjects_service import SubjectsService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

subject_repository = DynamoSubjectsRepository()
subject_service = SubjectsService(subject_repository)

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
        degree_id = event.get("pathParameters", {}).get("degreeId")
        subject_id = event.get("pathParameters", {}).get("subjectId")

        if not subject_id or not degree_id:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error":
                                    "Falta el parámetro degree_id/subject_id"})
            }
        subject_data = subject_service.get_subject_details(degree_id,
                                                          subject_id)

        if not subject_data:
            return {
                "statusCode": 404,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error":
                                    "Materia no encontrada en la carrera seleccionada"})
            }

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(subject_data.dict())
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Error interno: {str(e)}"})
        }
