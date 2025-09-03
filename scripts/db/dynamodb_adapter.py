import boto3
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from scripts.db.database_factory import DatabaseInterface
from scripts.db.config import AWS_REGION, USERS_TABLE, COMPANIES_TABLE, SPOCS_TABLE, INVOICES_TABLE

class DynamoDBAdapter(DatabaseInterface):
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        self.users_table = self.dynamodb.Table(USERS_TABLE)
        self.companies_table = self.dynamodb.Table(COMPANIES_TABLE)
        self.spocs_table = self.dynamodb.Table(SPOCS_TABLE)
        self.invoices_table = self.dynamodb.Table(INVOICES_TABLE)
    
    def create_user(self, username: str, hashed_password: str) -> Dict[str, Any]:
        user_data = {
            'username': username,
            'hashed_password': hashed_password,
            'created_date': datetime.now(timezone.utc).isoformat()
        }
        self.users_table.put_item(Item=user_data)
        return {'username': username}
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.users_table.get_item(Key={'username': username})
            return response.get('Item')
        except ClientError:
            return None
    
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
    
    def _get_next_id(self, table_type: str) -> int:
        """Get next auto-increment ID for a table type"""
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
            # First time - initialize counter
            counter_table.put_item(Item={'table_name': table_type, 'next_id': 1})
            return 1