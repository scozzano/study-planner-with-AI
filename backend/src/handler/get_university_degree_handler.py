import json
import logging

from src.repository.university_repository import DynamoUniversityRepository
from src.services.university_service import UniversityService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

university_repository = DynamoUniversityRepository()
university_service = UniversityService(university_repository)

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
        degree_id = event.get("pathParameters", {}).get("degree_id")

        if not degree_id:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Falta el parámetro degreeId"})
            }

        university_data = university_service.get_university_degree(degree_id)

        if not university_data:
            return {
                "statusCode": 404,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Carrera no encontrada"})
            }

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(university_data.dict())
        }

    except ValueError as ve:
        logger.warning(f"Carrera no encontrada: {str(ve)}")
        return {
            "statusCode": 404,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(ve)})
        }
    except Exception as e:
        logger.error(f"Error interno: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Error interno: {str(e)}"})
        }
