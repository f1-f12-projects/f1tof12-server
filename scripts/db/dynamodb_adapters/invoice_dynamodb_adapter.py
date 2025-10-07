from typing import Optional, List, Dict, Any
from botocore.exceptions import ClientError
from scripts.db.config import INVOICES_TABLE
from .base_dynamodb_adapter import BaseDynamoDBAdapter

class InvoiceDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.invoices_table = self.dynamodb.Table(INVOICES_TABLE)
    
    def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        invoice_id = self._get_next_id('invoices')
        invoice_data['id'] = invoice_id
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
            response = self.invoices_table.get_item(Key={'id': invoice_id})
            return response.get('Item')
        except ClientError:
            return None
    
    def update_invoice(self, invoice_id: int, update_data: Dict[str, Any]) -> bool:
        try:
            update_expression = "SET "
            expression_values = {}
            
            for key, value in update_data.items():
                update_expression += f"{key} = :{key}, "
                expression_values[f":{key}"] = value
            
            self.invoices_table.update_item(
                Key={'id': invoice_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except ClientError:
            return False