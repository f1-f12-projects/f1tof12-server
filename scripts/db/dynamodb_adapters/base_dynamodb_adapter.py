import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from scripts.db.config import AWS_REGION

class BaseDynamoDBAdapter:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    
    def _get_next_id(self, table_type: str) -> int:
        counter_table = self.dynamodb.Table('f1tof12-counters')
        try:
            response = counter_table.update_item(
                Key={'table_name': table_type},
                UpdateExpression='ADD next_id :inc',
                ExpressionAttributeValues={':inc': 1},
                ReturnValues='UPDATED_NEW'
            )
            return int(response['Attributes']['next_id'])
        except ClientError:
            counter_table.put_item(Item={'table_name': table_type, 'next_id': 1})
            return 1