from typing import Optional, Dict, Any
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from scripts.db.config import USERS_TABLE
from .base_dynamodb_adapter import BaseDynamoDBAdapter

class UserDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.users_table = self.dynamodb.Table(USERS_TABLE)
    
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