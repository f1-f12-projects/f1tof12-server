from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from scripts.db.config import COMPANIES_TABLE
from .base_dynamodb_adapter import BaseDynamoDBAdapter

class CompanyDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.companies_table = self.dynamodb.Table(COMPANIES_TABLE)
    
    def create_company(self, name: str, spoc: str, email_id: str, status: str = "active") -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        company_id = self._get_next_id('companies')
        company_data = {
            'id': company_id,
            'name': name,
            'spoc': spoc,
            'email_id': email_id,
            'status': status,
            'created_date': now,
            'updated_date': now
        }
        self.companies_table.put_item(Item=company_data)
        return company_data
    
    def get_company_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.companies_table.scan(
                FilterExpression='#name = :name',
                ExpressionAttributeNames={'#name': 'name'},
                ExpressionAttributeValues={':name': name}
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except ClientError:
            return None
    
    def list_companies(self) -> List[Dict[str, Any]]:
        try:
            response = self.companies_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []
    
    def list_active_companies(self) -> List[Dict[str, Any]]:
        try:
            response = self.companies_table.scan(
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'active'}
            )
            return response.get('Items', [])
        except ClientError:
            return []
    
    def update_company(self, company_id: int, update_data: Dict[str, Any]) -> bool:
        try:
            update_expression = "SET "
            expression_values = {}
            
            for key, value in update_data.items():
                update_expression += f"{key} = :{key}, "
                expression_values[f":{key}"] = value
            
            update_expression += "updated_date = :updated_date"
            expression_values[":updated_date"] = datetime.now(timezone.utc).isoformat()
            
            self.companies_table.update_item(
                Key={'id': company_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except ClientError:
            return False