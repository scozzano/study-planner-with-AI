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
        subject_data = subject_service.get_subjects()

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps([subject.dict() for subject in subject_data])

        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Error interno: {str(e)}"})
        }
