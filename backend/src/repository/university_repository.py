from decimal import Decimal
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Key

from src.model.records.university_record import UniversityRecord


def convert_decimals_to_int(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimals_to_int(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_int(item) for item in obj]
    else:
        return obj


class DynamoUniversityRepository:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('AdaProjectTable')

    def get_degree(self, degreeId: str) -> Optional[UniversityRecord]:
        try:
            response = self.table.get_item(
                Key={
                    'PK': f'UNIVERSITY#',
                    'SK': f'DEGREE#{degreeId}'
                }
            )

            item = response.get('Item')
            if item:
                item = convert_decimals_to_int(item)

                if 'subjects' not in item:
                    item['subjects'] = []
                elif not isinstance(item['subjects'], list):
                    item['subjects'] = []

                if 'id' not in item:
                    try:
                        item['id'] = int(degreeId)
                    except ValueError:
                        item['id'] = None

                return UniversityRecord(**item)
            return None

        except Exception as e:
            print(f"Error getting degree {degreeId}: {e}")
            return None
