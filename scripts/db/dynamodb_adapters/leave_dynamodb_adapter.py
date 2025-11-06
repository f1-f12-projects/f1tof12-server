from typing import List, Dict, Any, Optional
from scripts.db.dynamodb_adapters.base_dynamodb_adapter import BaseDynamoDBAdapter
from scripts.db.config import LEAVES_TABLE, LEAVE_BALANCES_TABLE
from datetime import datetime

class LeaveDynamoDBAdapter(BaseDynamoDBAdapter):
    
    def __init__(self):
        super().__init__()
        self.leave_table_name = LEAVES_TABLE
        self.balance_table_name = LEAVE_BALANCES_TABLE
    
    def create_leave(self, leave_data: Dict[str, Any]) -> int:
        leave_id = self._get_next_id('leaves')
        item = {
            'id': leave_id,
            'username': leave_data['username'],
            'leave_type': leave_data['leave_type'],
            'start_date': leave_data['start_date'].isoformat(),
            'end_date': leave_data['end_date'].isoformat(),
            'days': leave_data['days'],
            'reason': leave_data['reason'],
            'status': leave_data.get('status', 'pending'),
            'created_date': datetime.now().isoformat(),
            'updated_date': datetime.now().isoformat()
        }
        
        table = self.dynamodb.Table(self.leave_table_name)
        table.put_item(Item=item)
        return leave_id
    
    def get_user_leaves(self, username: str) -> List[Dict]:
        table = self.dynamodb.Table(self.leave_table_name)
        response = table.scan(
            FilterExpression='username = :username',
            ExpressionAttributeValues={':username': username}
        )
        return response.get('Items', [])
    
    def get_pending_leaves(self) -> List[Dict]:
        table = self.dynamodb.Table(self.leave_table_name)
        response = table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'pending'}
        )
        return response.get('Items', [])
    
    def get_all_leaves(self) -> List[Dict]:
        table = self.dynamodb.Table(self.leave_table_name)
        response = table.scan()
        return response.get('Items', [])
    
    def get_leave_by_id(self, leave_id: int) -> Optional[Dict]:
        table = self.dynamodb.Table(self.leave_table_name)
        response = table.get_item(Key={'id': leave_id})
        return response.get('Item')
    
    def update_leave(self, leave_id: int, update_data: Dict[str, Any]) -> bool:
        update_parts = []
        expression_values = {}
        expression_names = {}
        
        for key, value in update_data.items():
            # Convert datetime objects to ISO format strings
            if isinstance(value, datetime):
                value = value.isoformat()
            
            if key == 'status':
                update_parts.append("#status = :status")
                expression_names['#status'] = 'status'
                expression_values[':status'] = value
            else:
                update_parts.append(f"{key} = :{key}")
                expression_values[f":{key}"] = value
        
        update_parts.append("updated_date = :updated_date")
        expression_values[":updated_date"] = datetime.now().isoformat()
        
        update_expression = "SET " + ", ".join(update_parts)
        
        try:
            table = self.dynamodb.Table(self.leave_table_name)
            update_params = {
                'Key': {'id': leave_id},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values
            }
            if expression_names:
                update_params['ExpressionAttributeNames'] = expression_names
            
            table.update_item(**update_params)
            return True
        except Exception as e:
            print(f"DynamoDB update error: {e}")
            return False
    
    def create_leave_balance(self, username: str) -> int:
        balance_id = self._get_next_id('leave_balances')
        item = {
            'id': balance_id,
            'username': username,
            'annual_leave': 0,
            'sick_leave': 0,
            'casual_leave': 0,
            'year': datetime.now().year,
            'created_date': datetime.now().isoformat(),
            'updated_date': datetime.now().isoformat()
        }
        
        table = self.dynamodb.Table(self.balance_table_name)
        table.put_item(Item=item)
        return balance_id
    
    def get_leave_balance(self, username: str) -> Optional[Dict]:
        table = self.dynamodb.Table(self.balance_table_name)
        response = table.scan(
            FilterExpression='username = :username',
            ExpressionAttributeValues={':username': username}
        )
        items = response.get('Items', [])
        return items[0] if items else None
    
    def update_leave_balance(self, username: str, update_data: Dict[str, Any]) -> bool:
        balance = self.get_leave_balance(username)
        if not balance:
            return False
        
        update_expression = "SET "
        expression_values = {}
        
        for key, value in update_data.items():
            update_expression += f"{key} = :{key}, "
            expression_values[f":{key}"] = value
        
        update_expression += "updated_date = :updated_date"
        expression_values[":updated_date"] = datetime.now().isoformat()
        
        try:
            table = self.dynamodb.Table(self.balance_table_name)
            table.update_item(
                Key={'id': balance['id']},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except Exception:
            return False