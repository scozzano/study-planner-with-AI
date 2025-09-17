import json
from datetime import datetime
from decimal import Decimal

import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('AdaProjectTable')

def lambda_handler(event, context):

    try:
        path_parameters = event.get('pathParameters', {})
        student_id = path_parameters.get('student_id')
        degree_id = path_parameters.get('degree_id')

        query_parameters = event.get('queryStringParameters') or {}
        algorithm_filter = query_parameters.get('algorithm', '').lower()
        start_day = query_parameters.get('start_day')
        end_day = query_parameters.get('end_day')

        if not student_id or not degree_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS'
                },
                'body': json.dumps({
                    'error': 'student_id y degree_id son requeridos'
                })
            }

        if algorithm_filter and algorithm_filter not in ['asb', 'rf', 'pm', 'spm']:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS'
                },
                'body': json.dumps({
                    'error': f'Algoritmo "{algorithm_filter}" no válido. Algoritmos soportados: asb, rf, pm, spm'
                })
            }

        if start_day or end_day:
            try:
                from datetime import datetime

                if start_day:
                    start_date = datetime.strptime(start_day, '%Y-%m-%d')
                else:
                    start_date = None

                if end_day:
                    end_date = datetime.strptime(end_day, '%Y-%m-%d')
                else:
                    end_date = None

                if start_date and end_date and start_date > end_date:
                    raise ValueError("start_day no puede ser posterior a end_day")

            except ValueError as e:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'GET, OPTIONS'
                    },
                    'body': json.dumps({
                        'error': f'Error en formato de fechas: {str(e)}. Use formato YYYY-MM-DD'
                    })
                }

        pk = f"DEGREE#{degree_id}"
        sk = f"LOGS#{student_id}"

        print(f"[DEBUG] Buscando logs para PK: {pk}, SK: {sk}")

        response = table.get_item(
            Key={
                'PK': pk,
                'SK': sk
            }
        )

        if 'Item' not in response:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS'
                },
                'body': json.dumps({
                    'student_id': student_id,
                    'degree_id': degree_id,
                    'logs': [],
                    'total_logs': 0,
                    'total_logs_before_filter': 0,
                    'algorithm_filter': algorithm_filter if algorithm_filter else None,
                    'start_day': start_day,
                    'end_day': end_day,
                    'message': 'No se encontraron logs para este estudiante'
                })
            }

        item = response['Item']
        logs = item.get('logs', [])

        def convert_decimals(obj):
            if isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: convert_decimals(value) for key, value in obj.items()}
            elif isinstance(obj, Decimal):
                return int(obj) if obj % 1 == 0 else float(obj)
            else:
                return obj

        logs = convert_decimals(logs)

        original_count = len(logs)
        filtered_logs = []

        for log in logs:
            if algorithm_filter:
                request_algorithm = log.get('request', {}).get('algorithm', '').lower()
                if request_algorithm != algorithm_filter:
                    continue

            if start_day or end_day:
                log_date_str = log.get('date', '')
                if log_date_str:
                    try:
                        log_date = datetime.strptime(log_date_str[:10], '%Y-%m-%d')

                        if start_day and log_date < start_date:
                            continue
                        if end_day and log_date > end_date:
                            continue
                    except (ValueError, TypeError):
                        pass

            filtered_logs.append(log)

        logs = filtered_logs

        logs.sort(key=lambda x: x.get('date', ''), reverse=True)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': json.dumps({
                'student_id': student_id,
                'degree_id': degree_id,
                'logs': logs,
                'total_logs': len(logs),
                'total_logs_before_filter': original_count,
                'algorithm_filter': algorithm_filter if algorithm_filter else None,
                'start_day': start_day,
                'end_day': end_day,
                'last_updated': item.get('last_updated', 'N/A'),
                'message': f'Logs obtenidos exitosamente. {len(logs)} logs mostrados de {original_count} totales.'
            })
        }

    except Exception as e:
        print(f"[ERROR] Error al obtener logs: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': json.dumps({
                'error': f'Error interno del servidor: {str(e)}'
            })
        }
