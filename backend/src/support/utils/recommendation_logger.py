import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('AdaProjectTable')

def convert_floats_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    else:
        return obj

def log_recommendation(student_id, degree_id, request_data, response_data):
    try:
        pk = f"DEGREE#{degree_id}"
        sk = f"LOGS#{student_id}"

        new_log = {
            'date': datetime.utcnow().isoformat() + 'Z',
            'request': convert_floats_to_decimal(request_data),
            'response': convert_floats_to_decimal(response_data)
        }

        print(f"[DEBUG] Agregando log para PK: {pk}, SK: {sk}")
        print(f"[DEBUG] Nuevo log creado con fecha: {new_log['date']}")

        try:
            response = table.get_item(
                Key={
                    'PK': pk,
                    'SK': sk
                }
            )

            if 'Item' in response:
                existing_logs = response['Item'].get('logs', [])
                existing_logs.append(new_log)

                table.update_item(
                    Key={
                        'PK': pk,
                        'SK': sk
                    },
                    UpdateExpression='SET logs = :logs, last_updated = :last_updated',
                    ExpressionAttributeValues={
                        ':logs': existing_logs,
                        ':last_updated': datetime.utcnow().isoformat() + 'Z'
                    }
                )

                print(f"[DEBUG] Log agregado exitosamente. Total logs: {len(existing_logs)}")

            else:
                new_item = {
                    'PK': pk,
                    'SK': sk,
                    'logs': [new_log],
                    'created_at': datetime.utcnow().isoformat() + 'Z',
                    'last_updated': datetime.utcnow().isoformat() + 'Z'
                }

                table.put_item(Item=new_item)
                print(f"[DEBUG] Nuevo registro de logs creado. Total logs: 1")

        except Exception as e:
            print(f"[ERROR] Error al actualizar logs en DynamoDB: {str(e)}")
            try:
                new_item = {
                    'PK': pk,
                    'SK': sk,
                    'logs': [new_log],
                    'created_at': datetime.utcnow().isoformat() + 'Z',
                    'last_updated': datetime.utcnow().isoformat() + 'Z'
                }

                table.put_item(Item=new_item)
                print(f"[DEBUG] Registro de logs creado como fallback")

            except Exception as fallback_error:
                print(f"[ERROR] Error crítico al crear logs: {str(fallback_error)}")
                raise fallback_error

    except Exception as e:
        print(f"[ERROR] Error general en log_recommendation: {str(e)}")
        pass

def get_student_logs(student_id, degree_id, algorithm_filter=None, start_day=None, end_day=None):
    try:
        pk = f"DEGREE#{degree_id}"
        sk = f"LOGS#{student_id}"

        response = table.get_item(
            Key={
                'PK': pk,
                'SK': sk
            }
        )

        if 'Item' in response:
            logs = response['Item'].get('logs', [])

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

            filtered_logs = []

            for log in logs:
                if algorithm_filter:
                    algorithm_filter_lower = algorithm_filter.lower()
                    request_algorithm = log.get('request', {}).get('algorithm', '').lower()
                    if request_algorithm != algorithm_filter_lower:
                        continue

                if start_day or end_day:
                    log_date_str = log.get('date', '')
                    if log_date_str:
                        try:
                            from datetime import datetime
                            log_date = datetime.strptime(log_date_str[:10], '%Y-%m-%d')

                            if start_day:
                                start_date = datetime.strptime(start_day, '%Y-%m-%d')
                                if log_date < start_date:
                                    continue
                            if end_day:
                                end_date = datetime.strptime(end_day, '%Y-%m-%d')
                                if log_date > end_date:
                                    continue
                        except (ValueError, TypeError):
                            pass

                filtered_logs.append(log)

            logs = filtered_logs

            logs.sort(key=lambda x: x.get('date', ''), reverse=True)

            return logs
        else:
            return []

    except Exception as e:
        print(f"[ERROR] Error al obtener logs: {str(e)}")
        return []
