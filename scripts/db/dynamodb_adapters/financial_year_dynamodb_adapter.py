from typing import List, Dict, Any, Optional
from scripts.db.dynamodb_adapters.base_dynamodb_adapter import BaseDynamoDBAdapter
from scripts.db.config import FINANCIAL_YEARS_TABLE
from datetime import datetime

class FinancialYearDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.table_name = FINANCIAL_YEARS_TABLE
    
    def create_financial_year(self, year: int, start_date, end_date, is_active: bool = False) -> int:
        if is_active:
            # Deactivate all other years
            all_years = self.get_all_financial_years()
            for fy in all_years:
                if fy.get('is_active'):
                    self.update_financial_year(fy['id'], {'is_active': False})
        
        year_id = self._get_next_id('financial_years')
        item = {
            'id': year_id,
            'year': year,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'is_active': is_active,
            'created_date': datetime.now().isoformat(),
            'updated_date': datetime.now().isoformat()
        }
        
        table = self.dynamodb.Table(self.table_name)
        table.put_item(Item=item)
        return year_id
    
    def get_all_financial_years(self) -> List[Dict[str, Any]]:
        table = self.dynamodb.Table(self.table_name)
        response = table.scan()
        return response.get('Items', [])
    
    def get_active_financial_year(self) -> Optional[Dict[str, Any]]:
        table = self.dynamodb.Table(self.table_name)
        response = table.scan(
            FilterExpression='is_active = :active',
            ExpressionAttributeValues={':active': True}
        )
        items = response.get('Items', [])
        return items[0] if items else None
    
    def get_financial_year_by_id(self, year_id: int) -> Optional[Dict[str, Any]]:
        table = self.dynamodb.Table(self.table_name)
        response = table.get_item(Key={'id': year_id})
        return response.get('Item')
    
    def set_active_financial_year(self, year_id: int) -> bool:
        # Deactivate all years
        all_years = self.get_all_financial_years()
        for fy in all_years:
            if fy.get('is_active'):
                self.update_financial_year(fy['id'], {'is_active': False})
        
        # Activate the specified year
        return self.update_financial_year(year_id, {'is_active': True})
    
    def update_financial_year(self, year_id: int, update_data: Dict[str, Any]) -> bool:
        if update_data.get('is_active'):
            # Deactivate all other years
            all_years = self.get_all_financial_years()
            for fy in all_years:
                if fy.get('is_active') and fy['id'] != year_id:
                    table = self.dynamodb.Table(self.table_name)
                    table.update_item(
                        Key={'id': fy['id']},
                        UpdateExpression='SET is_active = :active, updated_date = :updated',
                        ExpressionAttributeValues={':active': False, ':updated': datetime.now().isoformat()}
                    )
        
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
                Key={'id': year_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except Exception:
            return False
    
