from typing import List, Dict, Any
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from scripts.db.config import SPOCS_TABLE
from .base_dynamodb_adapter import BaseDynamoDBAdapter

class SPOCDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.spocs_table = self.dynamodb.Table(SPOCS_TABLE)
    
    def create_spoc(self, company_id: int, name: str, phone: str, email_id: str, location: str, status: str = "active") -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        spoc_id = self._get_next_id('spocs')
        spoc_data = {
            'id': spoc_id,
            'company_id': company_id,
            'name': name,
            'phone': phone,
            'email_id': email_id,
            'location': location,
            'status': status,
            'created_date': now,
            'updated_date': now
        }
        self.spocs_table.put_item(Item=spoc_data)
        return spoc_data
    
    def list_spocs(self) -> List[Dict[str, Any]]:
        try:
            response = self.spocs_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []
    
    def update_spoc(self, spoc_id: int, update_data: Dict[str, Any]) -> bool:
        try:
            from decimal import Decimal
            update_expression = "SET "
            expression_values = {}
            
            for key, value in update_data.items():
                # Convert float to Decimal for DynamoDB compatibility
                if isinstance(value, float):
                    value = Decimal(str(value))
                update_expression += f"{key} = :{key}, "
                expression_values[f":{key}"] = value
            
            update_expression += "updated_date = :updated_date"
            expression_values[":updated_date"] = datetime.now(timezone.utc).isoformat()
            
            from decimal import Decimal
            self.spocs_table.update_item(
                Key={'id': Decimal(str(spoc_id))},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except ClientError:
            return False
    
    def get_spocs_by_company(self, company_id: int) -> List[Dict[str, Any]]:
        try:
            response = self.spocs_table.scan(
                FilterExpression='company_id = :company_id AND #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':company_id': company_id, ':status': 'active'}
            )
            return response.get('Items', [])
        except ClientError:
            return []