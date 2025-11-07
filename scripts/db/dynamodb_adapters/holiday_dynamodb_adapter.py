from typing import List, Dict, Any, Optional
from scripts.db.dynamodb_adapters.base_dynamodb_adapter import BaseDynamoDBAdapter
from scripts.db.config import HOLIDAYS_TABLE, USER_HOLIDAY_SELECTIONS_TABLE
from datetime import datetime

class HolidayDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.table_name = HOLIDAYS_TABLE
        self.user_selections_table = USER_HOLIDAY_SELECTIONS_TABLE
    
    def create_holiday(self, financial_year_id: int, name: str, date, is_mandatory: bool = True) -> int:
        holiday_id = self._get_next_id('holidays')
        item = {
            'id': holiday_id,
            'financial_year_id': financial_year_id,
            'name': name,
            'date': date.isoformat(),
            'is_mandatory': is_mandatory,
            'created_date': datetime.now().isoformat(),
            'updated_date': datetime.now().isoformat()
        }
        
        table = self.dynamodb.Table(self.table_name)
        table.put_item(Item=item)
        return holiday_id
    
    def get_holidays_by_year(self, financial_year_id: int) -> List[Dict[str, Any]]:
        table = self.dynamodb.Table(self.table_name)
        response = table.scan(
            FilterExpression='financial_year_id = :fy_id',
            ExpressionAttributeValues={':fy_id': financial_year_id}
        )
        return response.get('Items', [])
    
    def get_holiday_by_id(self, holiday_id: int) -> Optional[Dict[str, Any]]:
        table = self.dynamodb.Table(self.table_name)
        response = table.get_item(Key={'id': holiday_id})
        return response.get('Item')
    
    def get_optional_holidays(self, financial_year_id: int) -> List[Dict[str, Any]]:
        items = self.get_holidays_by_year(financial_year_id)
        return [item for item in items if not item.get('is_mandatory', True)]
    
    def get_mandatory_holidays(self, financial_year_id: int) -> List[Dict[str, Any]]:
        items = self.get_holidays_by_year(financial_year_id)
        return [item for item in items if item.get('is_mandatory', True)]
    
    def update_holiday(self, holiday_id: int, update_data: Dict[str, Any]) -> bool:
        update_expression = "SET "
        expression_values = {}
        
        for key, value in update_data.items():
            update_expression += f"{key} = :{key}, "
            expression_values[f":{key}"] = value
        
        update_expression += "updated_date = :updated_date"
        expression_values[":updated_date"] = datetime.now().isoformat()
        
        try:
            table = self.dynamodb.Table(self.table_name)
            table.update_item(
                Key={'id': holiday_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except Exception:
            return False
    
    def delete_holiday(self, holiday_id: int) -> bool:
        try:
            table = self.dynamodb.Table(self.table_name)
            table.delete_item(Key={'id': holiday_id})
            return True
        except Exception:
            return False
    
    def select_optional_holidays(self, username: str, holiday_ids: List[int], financial_year_id: int) -> bool:
        table = self.dynamodb.Table(self.user_selections_table)
        
        # Remove existing selections
        response = table.scan(
            FilterExpression='username = :username AND financial_year_id = :fy_id',
            ExpressionAttributeValues={':username': username, ':fy_id': financial_year_id}
        )
        
        for item in response.get('Items', []):
            table.delete_item(Key={'id': item['id']})
        
        # Add new selections
        for holiday_id in holiday_ids:
            selection_id = self._get_next_id('user_holiday_selections')
            table.put_item(Item={
                'id': selection_id,
                'username': username,
                'holiday_id': holiday_id,
                'financial_year_id': financial_year_id,
                'created_date': datetime.now().isoformat()
            })
        
        return True
    
    def get_user_selected_holidays(self, username: str, financial_year_id: int) -> List[Dict[str, Any]]:
        table = self.dynamodb.Table(self.user_selections_table)
        
        response = table.scan(
            FilterExpression='username = :username AND financial_year_id = :fy_id',
            ExpressionAttributeValues={':username': username, ':fy_id': financial_year_id}
        )
        
        selections = response.get('Items', [])
        result = []
        
        for selection in selections:
            holiday = self.get_holiday_by_id(selection['holiday_id'])
            if holiday:
                holiday['selection_date'] = selection['created_date']
                result.append(holiday)
        
        return result
    
    def get_user_holidays_for_year(self, username: str, financial_year_id: int) -> Dict[str, Any]:
        mandatory = self.get_mandatory_holidays(financial_year_id)
        selected_optional = self.get_user_selected_holidays(username, financial_year_id)
        all_optional = self.get_optional_holidays(financial_year_id)
        
        return {
            "mandatory_holidays": mandatory,
            "selected_optional_holidays": selected_optional,
            "available_optional_holidays": all_optional
        }