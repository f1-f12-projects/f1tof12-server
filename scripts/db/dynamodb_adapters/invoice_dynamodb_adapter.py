from typing import Optional, List, Dict, Any
from botocore.exceptions import ClientError
from scripts.db.config import INVOICES_TABLE
from .base_dynamodb_adapter import BaseDynamoDBAdapter

class InvoiceDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.invoices_table = self.dynamodb.Table(INVOICES_TABLE)
    
    def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        from decimal import Decimal
        from datetime import date, datetime
        invoice_id = self._get_next_id('invoices')
        invoice_data['id'] = invoice_id
        
        # Convert float and date values for DynamoDB compatibility
        for key, value in invoice_data.items():
            if isinstance(value, float):
                invoice_data[key] = Decimal(str(value))
            elif isinstance(value, (date, datetime)):
                invoice_data[key] = value.isoformat()
        
        self.invoices_table.put_item(Item=invoice_data)
        return invoice_data
    
    def list_invoices(self) -> List[Dict[str, Any]]:
        try:
            response = self.invoices_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []
    
    def get_invoice(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        try:
            from decimal import Decimal
            response = self.invoices_table.get_item(Key={'id': Decimal(str(invoice_id))})
            return response.get('Item')
        except ClientError:
            return None
    
    def update_invoice(self, invoice_id: int, update_data: Dict[str, Any]) -> bool:
        try:
            from decimal import Decimal
            from datetime import date, datetime
            update_expression = "SET "
            expression_values = {}
            
            for key, value in update_data.items():
                # Convert float and date values for DynamoDB compatibility
                if isinstance(value, float):
                    value = Decimal(str(value))
                elif isinstance(value, (date, datetime)):
                    value = value.isoformat()
                update_expression += f"{key} = :{key}, "
                expression_values[f":{key}"] = value
            
            self.invoices_table.update_item(
                Key={'id': Decimal(str(invoice_id))},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except ClientError:
            return False