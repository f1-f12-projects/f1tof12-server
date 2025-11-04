import time
from botocore.exceptions import ClientError
from scripts.db.lambda_dynamodb_pool import pool
from scripts.db.config import COUNTERS_TABLE

class BaseDynamoDBAdapter:
    def __init__(self):
        self.dynamodb = pool.get_resource()
    
    def _get_next_id(self, table_type: str) -> int:
        counter_table = self.dynamodb.Table(COUNTERS_TABLE)
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
    
    def _batch_scan_by_ids(self, table, ids, id_field, batch_size=100):
        """Scan table in batches filtering by list of IDs"""
        from decimal import Decimal
        results = {}
        
        if not ids:
            return results
            
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            
            filter_expr = ' OR '.join([f'{id_field} = :id{j}' for j in range(len(batch_ids))])
            expr_values = {f':id{j}': Decimal(str(id_val)) for j, id_val in enumerate(batch_ids)}
            
            response = table.scan(
                FilterExpression=filter_expr,
                ExpressionAttributeValues=expr_values
            )
            
            for item in response.get('Items', []):
                item_id = item.get(id_field)
                if isinstance(item_id, Decimal):
                    item_id = int(item_id)
                results[item_id] = item
                
        return results