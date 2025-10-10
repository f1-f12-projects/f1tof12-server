from typing import Optional, List, Dict, Any
from botocore.exceptions import ClientError
from scripts.db.config import PROFILES_TABLE, PROFILE_STATUSES_TABLE
from .base_dynamodb_adapter import BaseDynamoDBAdapter

class ProfileDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.profiles_table = self.dynamodb.Table(PROFILES_TABLE)
        self.profile_statuses_table = self.dynamodb.Table(PROFILE_STATUSES_TABLE)
    
    def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        profile_id = self._get_next_id('profiles')
        profile_data['profile_id'] = profile_id
        self.profiles_table.put_item(Item=profile_data)
        return profile_data
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        try:
            response = self.profiles_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []
    
    def get_profile(self, profile_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = self.profiles_table.get_item(Key={'profile_id': profile_id})
            return response.get('Item')
        except ClientError:
            return None
    
    def update_profile(self, profile_id: int, update_data: Dict[str, Any]) -> bool:
        try:
            update_expression = "SET "
            expression_values = {}
            
            for key, value in update_data.items():
                update_expression += f"{key} = :{key}, "
                expression_values[f":{key}"] = value
            
            update_expression = update_expression.rstrip(', ')
            
            self.profiles_table.update_item(
                Key={'profile_id': profile_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except ClientError:
            return False
    
    def list_profile_statuses(self) -> List[Dict[str, Any]]:
        try:
            response = self.profile_statuses_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []