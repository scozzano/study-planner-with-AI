import base64
import json
import logging

from src.model.requests.schooling_model import SchoolingRequest
from src.repository.students_repository import DynamoStudentsRepository
from src.services.student_service import StudentService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

students_repository = DynamoStudentsRepository()
students_services = StudentService(students_repository)

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
        logger.info(f"Event recibido: {json.dumps(event, default=str)}")

        body_str = event.get("body")
        if not body_str:
            logger.error("No se encontró body en el evento")
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "No se encontró body en la solicitud"})
            }

        try:
            body = json.loads(body_str)
            logger.info(f"Body parseado: {json.dumps(body, default=str)}")
        except json.JSONDecodeError as je:
            logger.error(f"Error al parsear JSON: {str(je)}")
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Error al parsear JSON: {str(je)}"})
            }

        try:
            request_data = SchoolingRequest(**body)
            logger.info("Request data validado correctamente")
        except Exception as ve:
            logger.error(f"Error de validación: {str(ve)}")
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Error de validación: {str(ve)}"})
            }

        try:
            pdf_bytes = base64.b64decode(request_data.file)
            logger.info(f"PDF decodificado, tamaño: {len(pdf_bytes)} bytes")
        except Exception as de:
            logger.error(f"Error al decodificar PDF: {str(de)}")
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Error al decodificar PDF: {str(de)}"})
            }

        try:
            result = students_services.upload_schooling(pdf_bytes)
            logger.info(f"Escolaridad procesada exitosamente: {json.dumps(result, default=str)}")
        except Exception as pe:
            logger.error(f"Error al procesar escolaridad: {str(pe)}")
            return {
                "statusCode": 500,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Error al procesar escolaridad: {str(pe)}"})
            }

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "message": "La escolaridad fue procesada exitosamente",
                "summary": result
                })
        }

    except Exception as e:
        logger.error(f"Error inesperado al procesar la escolaridad: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Error inesperado: {str(e)}"})
        }
