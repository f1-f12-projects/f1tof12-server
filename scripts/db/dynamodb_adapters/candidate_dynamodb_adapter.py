from typing import Optional, List, Dict, Any
from botocore.exceptions import ClientError
from scripts.db.config import CANDIDATES_TABLE, CANDIDATE_STATUSES_TABLE
from .base_dynamodb_adapter import BaseDynamoDBAdapter

class CandidateDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.candidates_table = self.dynamodb.Table(CANDIDATES_TABLE)
        self.candidate_statuses_table = self.dynamodb.Table(CANDIDATE_STATUSES_TABLE)
    
    def create_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        candidate_id = self._get_next_id('candidates')
        candidate_data['candidate_id'] = candidate_id
        self.candidates_table.put_item(Item=candidate_data)
        return candidate_data
    
    def list_candidates(self) -> List[Dict[str, Any]]:
        try:
            response = self.candidates_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []
    
    def get_candidate(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = self.candidates_table.get_item(Key={'candidate_id': candidate_id})
            return response.get('Item')
        except ClientError:
            return None
    
    def update_candidate(self, candidate_id: int, update_data: Dict[str, Any]) -> bool:
        try:
            update_expression = "SET "
            expression_values = {}
            
            for key, value in update_data.items():
                update_expression += f"{key} = :{key}, "
                expression_values[f":{key}"] = value
            
            update_expression = update_expression.rstrip(', ')
            
            self.candidates_table.update_item(
                Key={'candidate_id': candidate_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except ClientError:
            return False
    
    def list_candidate_statuses(self) -> List[Dict[str, Any]]:
        try:
            response = self.candidate_statuses_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []