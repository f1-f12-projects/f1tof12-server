from typing import Optional, List, Dict, Any
from botocore.exceptions import ClientError
from scripts.db.config import REQUIREMENTS_TABLE, REQUIREMENT_STATUSES_TABLE
from .base_dynamodb_adapter import BaseDynamoDBAdapter

class RequirementDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.requirements_table = self.dynamodb.Table(REQUIREMENTS_TABLE)
        self.requirement_statuses_table = self.dynamodb.Table(REQUIREMENT_STATUSES_TABLE)
    
    def create_requirement(self, requirement_data: Dict[str, Any]) -> Dict[str, Any]:
        requirement_id = self._get_next_id('requirements')
        requirement_data['requirement_id'] = requirement_id
        self.requirements_table.put_item(Item=requirement_data)
        return requirement_data
    
    def list_requirements(self) -> List[Dict[str, Any]]:
        try:
            response = self.requirements_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []
    
    def get_requirement(self, requirement_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = self.requirements_table.get_item(Key={'requirement_id': requirement_id})
            return response.get('Item')
        except ClientError:
            return None
    
    def update_requirement(self, requirement_id: int, update_data: Dict[str, Any]) -> bool:
        try:
            update_expression = "SET "
            expression_values = {}
            
            for key, value in update_data.items():
                update_expression += f"{key} = :{key}, "
                expression_values[f":{key}"] = value
            
            update_expression = update_expression.rstrip(', ')
            
            self.requirements_table.update_item(
                Key={'requirement_id': requirement_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except ClientError:
            return False
    
    def list_requirement_statuses(self) -> List[Dict[str, Any]]:
        try:
            response = self.requirement_statuses_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []
    
    def get_open_requirements_by_company(self, company_id: int) -> List[Dict[str, Any]]:
        try:
            response = self.requirements_table.scan(
                FilterExpression='company_id = :company_id AND status_id IN :open_statuses',
                ExpressionAttributeValues={
                    ':company_id': company_id,
                    ':open_statuses': [1, 2, 3]
                }
            )
            return response.get('Items', [])
        except ClientError:
            return []
    
    def get_open_requirements_by_company_and_recruiter(self, company_id: int, recruiter_name: str) -> List[Dict[str, Any]]:
        from scripts.db.config import PROCESS_PROFILES_TABLE
        try:
            # Get requirements assigned to recruiter
            process_profiles_table = self.dynamodb.Table(PROCESS_PROFILES_TABLE)
            pp_response = process_profiles_table.scan(
                FilterExpression='recruiter_name = :recruiter_name',
                ExpressionAttributeValues={':recruiter_name': recruiter_name}
            )
            assigned_req_ids = [pp['requirement_id'] for pp in pp_response.get('Items', [])]
            
            if not assigned_req_ids:
                return []
            
            # Get open requirements for company that are assigned to recruiter
            response = self.requirements_table.scan(
                FilterExpression='company_id = :company_id AND status_id IN :open_statuses AND requirement_id IN :req_ids',
                ExpressionAttributeValues={
                    ':company_id': company_id,
                    ':open_statuses': [1, 2, 3],
                    ':req_ids': assigned_req_ids
                }
            )
            return response.get('Items', [])
        except ClientError:
            return []