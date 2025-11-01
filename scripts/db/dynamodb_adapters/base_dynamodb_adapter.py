import time
from botocore.exceptions import ClientError
from scripts.db.lambda_dynamodb_pool import pool

class BaseDynamoDBAdapter:
    def __init__(self):
        self.dynamodb = pool.get_resource()
    
    def _get_next_id(self, table_type: str) -> int:
        counter_table = self.dynamodb.Table('f1tof12-counters')
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = counter_table.update_item(
                    Key={'table_name': table_type},
                    UpdateExpression='ADD next_id :inc',
                    ExpressionAttributeValues={':inc': 1},
                    ReturnValues='UPDATED_NEW'
                )
                return int(response['Attributes']['next_id'])
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    counter_table.put_item(Item={'table_name': table_type, 'next_id': 1})
                    return 1
                elif e.response['Error']['Code'] in ['ProvisionedThroughputExceededException', 'ThrottlingException']:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                raise