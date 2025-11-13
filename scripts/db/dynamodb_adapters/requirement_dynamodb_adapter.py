from typing import Optional, List, Dict, Any
from botocore.exceptions import ClientError
from scripts.db.config import REQUIREMENTS_TABLE, REQUIREMENT_STATUSES_TABLE
from .base_dynamodb_adapter import BaseDynamoDBAdapter
import logging

logger = logging.getLogger(__name__)

class RequirementDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.requirements_table = self.dynamodb.Table(REQUIREMENTS_TABLE)
        self.requirement_statuses_table = self.dynamodb.Table(REQUIREMENT_STATUSES_TABLE)
    
    def create_requirement(self, requirement_data: Dict[str, Any]) -> Dict[str, Any]:
        from decimal import Decimal
        from datetime import date, datetime
        requirement_id = self._get_next_id('requirements')
        requirement_data['requirement_id'] = requirement_id
        
        # Convert float and date values for DynamoDB compatibility
        for key, value in requirement_data.items():
            if isinstance(value, float):
                requirement_data[key] = Decimal(str(value))
            elif isinstance(value, (date, datetime)):
                requirement_data[key] = value.isoformat()
        
        self.requirements_table.put_item(Item=requirement_data)
        return requirement_data
    
    def list_requirements(self) -> List[Dict[str, Any]]:
        try:
            response = self.requirements_table.scan(ConsistentRead=True)
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"[DB] DynamoDB scan failed: {str(e)}")
            return []
    
    def get_requirement(self, requirement_id: int) -> Optional[Dict[str, Any]]:
        try:
            from decimal import Decimal
            response = self.requirements_table.get_item(Key={'requirement_id': Decimal(str(requirement_id))})
            return response.get('Item')
        except ClientError:
            return None
    
    def update_requirement(self, requirement_id: int, update_data: Dict[str, Any]) -> bool:
        try:
            from decimal import Decimal
            from datetime import date, datetime
            
            # First check if the item exists
            existing_item = self.get_requirement(requirement_id)
            if not existing_item:
                return False
            
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
                'Key': {'requirement_id': Decimal(str(requirement_id))},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values
            }
            
            if expression_names:
                update_params['ExpressionAttributeNames'] = expression_names
            
            self.requirements_table.update_item(**update_params)
            return True
        except ClientError as e:
            print(f"ClientError updating requirement {requirement_id}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error updating requirement {requirement_id}: {e}")
            return False
    
    def list_requirement_statuses(self) -> List[Dict[str, Any]]:
        try:
            response = self.requirement_statuses_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []
    
    def get_open_requirements_by_company(self, company_id: int) -> List[Dict[str, Any]]:
        try:
            from decimal import Decimal
            response = self.requirements_table.scan(
                FilterExpression='company_id = :company_id AND (status_id = :status1 OR status_id = :status2 OR status_id = :status3)',
                ExpressionAttributeValues={
                    ':company_id': Decimal(str(company_id)),
                    ':status1': Decimal('1'),
                    ':status2': Decimal('2'),
                    ':status3': Decimal('3')
                },
                ConsistentRead=True
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
            from decimal import Decimal
            # Convert req_ids to Decimal
            decimal_req_ids = [Decimal(str(req_id)) for req_id in assigned_req_ids]
            
            response = self.requirements_table.scan(
                FilterExpression='company_id = :company_id AND (status_id = :status1 OR status_id = :status2 OR status_id = :status3)',
                ExpressionAttributeValues={
                    ':company_id': Decimal(str(company_id)),
                    ':status1': Decimal('1'),
                    ':status2': Decimal('2'),
                    ':status3': Decimal('3')
                },
                ConsistentRead=True
            )
            
            # Filter by assigned requirement IDs in Python since DynamoDB IN has limitations
            filtered_items = [item for item in response.get('Items', []) if item.get('requirement_id') in decimal_req_ids]
            return filtered_items
        except ClientError:
            return []