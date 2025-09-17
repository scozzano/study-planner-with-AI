import json
import os
import sys
import traceback

import boto3

sagemaker = boto3.client('sagemaker')
sagemaker_runtime = boto3.client('sagemaker-runtime')
dynamodb = boto3.resource('dynamodb')

sys.path.append('/opt/python')
try:
    from support.utils.recommendation_logger import log_recommendation
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from support.utils.recommendation_logger import log_recommendation

def get_latest_endpoint(algorithm: str, degree_id: str) -> str:
    """Obtener el endpoint más reciente para un algoritmo"""

    try:
        response = sagemaker.list_endpoints(
            NameContains=f"{algorithm}-endpoint",
            StatusEquals='InService'
        )

        if not response['Endpoints']:
            raise ValueError(f"No se encontraron endpoints activos para {algorithm}")

        endpoints = sorted(
            response['Endpoints'],
            key=lambda x: x['CreationTime'],
            reverse=True
        )

        endpoint_name = endpoints[0]['EndpointName']
        print(f"🎯 Usando endpoint más reciente: {endpoint_name}")

        return endpoint_name

    except sagemaker.exceptions.ClientError as e:
        raise ValueError(f"Error listando endpoints: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error obteniendo endpoint: {str(e)}")

def lambda_handler(event, context):
    """Handler principal de Lambda para predicciones SageMaker"""

    try:
        body = json.loads(event.get('body', '{}'))

        algorithm = body.get('algorithm', '').lower()
        if not algorithm:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Parámetro "algorithm" es requerido'})
            }

        if algorithm not in ['asb', 'rf', 'pm', 'spm']:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Algoritmo "{algorithm}" no soportado'})
            }

        degree_id = body.get('degree_id', '2491')
        endpoint_name = get_latest_endpoint(algorithm, degree_id)

        print(f"🎯 Usando endpoint: {endpoint_name}")

        prediction_data = {
            'algorithm': algorithm,
            **body
        }

        if 'studentId' in prediction_data:
            prediction_data['student_id'] = prediction_data['studentId']

        if 'degreeId' in prediction_data:
            prediction_data['degree_id'] = prediction_data['degreeId']

        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(prediction_data)
        )

        result = json.loads(response['Body'].read().decode())

        try:
            student_id = prediction_data.get('student_id') or prediction_data.get('studentId')
            if student_id:
                print(f"📝 Loggeando recomendación para estudiante: {student_id}")
                log_recommendation(
                    student_id=str(student_id),
                    degree_id=str(degree_id),
                    request_data=prediction_data,
                    response_data=result
                )
            else:
                print("⚠️ No se pudo extraer student_id para logging")
        except Exception as log_error:
            print(f"⚠️ Error en logging (no crítico): {str(log_error)}")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps(result)
        }

    except Exception as e:
        print(f"❌ Error en predicción: {str(e)}")
        print(f"📋 Traceback: {traceback.format_exc()}")

        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }
