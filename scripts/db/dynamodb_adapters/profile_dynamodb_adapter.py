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
        from decimal import Decimal
        from datetime import date, datetime
        profile_id = self._get_next_id('profiles')
        profile_data['id'] = profile_id
        
        # Convert float and date values for DynamoDB compatibility
        for key, value in profile_data.items():
            if isinstance(value, float):
                profile_data[key] = Decimal(str(value))
            elif isinstance(value, (date, datetime)):
                profile_data[key] = value.isoformat()
        
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
            from decimal import Decimal
            response = self.profiles_table.get_item(Key={'id': Decimal(str(profile_id))})
            return response.get('Item')
        except ClientError:
            return None
    
    def update_profile(self, profile_id: int, update_data: Dict[str, Any]) -> bool:
        try:
            from decimal import Decimal
            from datetime import date, datetime
            update_expression = "SET "
            expression_values = {}
            expression_names = {}
            
            # DynamoDB reserved keywords that need ExpressionAttributeNames
            reserved_keywords = {'location', 'status', 'role', 'name', 'date', 'time'}
            
            for key, value in update_data.items():
                # Convert float and date values for DynamoDB compatibility
                if isinstance(value, float):
                    value = Decimal(str(value))
                elif isinstance(value, (date, datetime)):
                    value = value.isoformat()
                
                # Handle reserved keywords
                if key.lower() in reserved_keywords:
                    attr_name = f"#{key}"
                    expression_names[attr_name] = key
                    update_expression += f"{attr_name} = :{key}, "
                else:
                    update_expression += f"{key} = :{key}, "
                
                expression_values[f":{key}"] = value
            
            update_expression = update_expression.rstrip(', ')
            
            update_params = {
                'Key': {'id': Decimal(str(profile_id))},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values
            }
            
            if expression_names:
                update_params['ExpressionAttributeNames'] = expression_names
            
            self.profiles_table.update_item(**update_params)
            return True
        except ClientError:
            return False
    
    def list_profile_statuses(self) -> List[Dict[str, Any]]:
        try:
            response = self.profile_statuses_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []