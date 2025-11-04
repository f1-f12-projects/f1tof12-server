from typing import Dict, Any
from botocore.exceptions import ClientError
from scripts.db.config import PROCESS_PROFILES_TABLE, PROFILES_TABLE, PROFILE_STATUSES_TABLE
from .base_dynamodb_adapter import BaseDynamoDBAdapter

class ProcessProfileDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.process_profiles_table = self.dynamodb.Table(PROCESS_PROFILES_TABLE)
        self.profiles_table = self.dynamodb.Table(PROFILES_TABLE)
        self.profile_statuses_table = self.dynamodb.Table(PROFILE_STATUSES_TABLE)
    
    def create_process_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Check if unassigned requirement exists (recruiter_name is empty)
            response = self.process_profiles_table.scan(
                FilterExpression='requirement_id = :req_id AND recruiter_name = :empty',
                ExpressionAttributeValues={
                    ':req_id': profile_data['requirement_id'],
                    ':empty': ''
                }
            )
            if response.get('Items'):
                existing = response['Items'][0]
                merged_data = {**existing, **profile_data, 'actively_working': 'Yes'}
                self.process_profiles_table.put_item(Item=merged_data)
                return merged_data
            
            # Check by recruiter_name for other cases
            response = self.process_profiles_table.scan(
                FilterExpression='requirement_id = :req_id AND recruiter_name = :recruiter',
                ExpressionAttributeValues={
                    ':req_id': profile_data['requirement_id'],
                    ':recruiter': profile_data['recruiter_name']
                }
            )
            if response.get('Items'):
                return response['Items'][0]
        except ClientError:
            pass
        
        from decimal import Decimal
        profile_id = self._get_next_id('process_profiles')
        profile_data['id'] = profile_id
        
        # Convert float values to Decimal for DynamoDB compatibility
        for key, value in profile_data.items():
            if isinstance(value, float):
                profile_data[key] = Decimal(str(value))
        
        self.process_profiles_table.put_item(Item=profile_data)
        return profile_data
    
    def upsert_process_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        from decimal import Decimal
        
        # Convert float values to Decimal for DynamoDB compatibility
        for key, value in profile_data.items():
            if isinstance(value, float):
                profile_data[key] = Decimal(str(value))
        
        try:
            profile_id = profile_data.get('profile_id')
            if profile_id is None or profile_id == 0:
                filter_expr = 'requirement_id = :req_id AND profile_id = :zero'
                expr_values = {':req_id': profile_data['requirement_id'], ':zero': 0}
            else:
                filter_expr = 'requirement_id = :req_id AND profile_id = :prof_id'
                expr_values = {':req_id': profile_data['requirement_id'], ':prof_id': profile_id}
            
            response = self.process_profiles_table.scan(
                FilterExpression=filter_expr,
                ExpressionAttributeValues=expr_values
            )
            
            if response.get('Items'):
                existing = response['Items'][0]
                merged_data = {**existing, **profile_data}
                self.process_profiles_table.put_item(Item=merged_data)
                return merged_data
            else:
                profile_id = self._get_next_id('process_profiles')
                profile_data['id'] = profile_id
                self.process_profiles_table.put_item(Item=profile_data)
                return profile_data
        except ClientError:
            profile_id = self._get_next_id('process_profiles')
            profile_data['id'] = profile_id
            self.process_profiles_table.put_item(Item=profile_data)
            return profile_data
    
    def get_profiles_by_requirement(self, requirement_id: int) -> list:
        try:
            response = self.process_profiles_table.scan(
                FilterExpression='requirement_id = :req_id AND attribute_exists(profile_id)',
                ExpressionAttributeValues={
                    ':req_id': requirement_id
                }
            )
            items = response.get('Items', [])
            # Filter for actively working profiles, defaulting to 'Yes' if not specified
            active_items = [item for item in items if item.get('actively_working', 'Yes') == 'Yes']
            return self._enrich_with_profile_stage(active_items)
        except ClientError:
            return []
    
    def get_active_profiles_by_requirement(self, requirement_id: int) -> list:
        try:
            response = self.process_profiles_table.scan(
                FilterExpression='requirement_id = :req_id AND actively_working = :active',
                ExpressionAttributeValues={
                    ':req_id': requirement_id,
                    ':active': 'Yes'
                }
            )
            return response.get('Items', [])
        except ClientError:
            return []
    
    def get_profiles_by_requirement_and_recruiter(self, requirement_id: int, recruiter_name: str) -> list:
        try:
            response = self.process_profiles_table.scan(
                FilterExpression='requirement_id = :req_id AND recruiter_name = :recruiter AND attribute_exists(profile_id)',
                ExpressionAttributeValues={
                    ':req_id': requirement_id,
                    ':recruiter': recruiter_name
                }
            )
            items = response.get('Items', [])
            # Filter for actively working profiles, defaulting to 'Yes' if not specified
            active_items = [item for item in items if item.get('actively_working', 'Yes') == 'Yes']
            return self._enrich_with_profile_stage(active_items)
        except ClientError:
            return []
    
    def update_actively_working(self, requirement_id: int, profile_id: int, actively_working: str) -> bool:
        try:
            response = self.process_profiles_table.scan(
                FilterExpression='requirement_id = :req_id AND profile_id = :prof_id',
                ExpressionAttributeValues={
                    ':req_id': requirement_id,
                    ':prof_id': profile_id
                }
            )
            
            if response.get('Items'):
                item = response['Items'][0]
                self.process_profiles_table.put_item(
                    Item={**item, 'actively_working': actively_working}
                )
                return True
            return False
        except ClientError:
            return False
    
    def update_actively_working_by_recruiter(self, requirement_id: int, recruiter_name: str, actively_working: str) -> bool:
        try:
            response = self.process_profiles_table.scan(
                FilterExpression='requirement_id = :req_id AND recruiter_name = :recruiter',
                ExpressionAttributeValues={
                    ':req_id': requirement_id,
                    ':recruiter': recruiter_name
                }
            )
            
            if response.get('Items'):
                item = response['Items'][0]
                self.process_profiles_table.put_item(
                    Item={**item, 'actively_working': actively_working}
                )
                return True
            return False
        except ClientError:
            return False
    
    def update_process_profile_recruiter(self, requirement_id: int, recruiter_name: str) -> bool:
        try:
            response = self.process_profiles_table.scan(
                FilterExpression='requirement_id = :req_id',
                ExpressionAttributeValues={':req_id': requirement_id}
            )
            
            if response.get('Items'):
                item = response['Items'][0]
                self.process_profiles_table.put_item(
                    Item={**item, 'recruiter_name': recruiter_name}
                )
                return True
            return False
        except ClientError:
            return False
    
    def update_process_profile_remarks(self, requirement_id: int, profile_id: int, remarks: str = None) -> bool:
        try:
            response = self.process_profiles_table.scan(
                FilterExpression='requirement_id = :req_id AND profile_id = :prof_id',
                ExpressionAttributeValues={
                    ':req_id': requirement_id,
                    ':prof_id': profile_id
                }
            )
            
            if response.get('Items'):
                item = response['Items'][0]
                self.process_profiles_table.put_item(
                    Item={**item, 'remarks': remarks}
                )
                return True
            return False
        except ClientError:
            return False
    
    def update_process_profile_profile(self, requirement_id: int, profile_id: int) -> bool:
        try:
            response = self.process_profiles_table.scan(
                FilterExpression='requirement_id = :req_id',
                ExpressionAttributeValues={':req_id': requirement_id}
            )
            
            if response.get('Items'):
                item = response['Items'][0]
                self.process_profiles_table.put_item(
                    Item={**item, 'profile_id': profile_id}
                )
                return True
            return False
        except ClientError:
            return False
    
    def _enrich_with_profile_stage(self, process_profiles: list) -> list:
        """Get full profile data with stage information"""
        try:
            # Get all profile statuses
            status_response = self.profile_statuses_table.scan()
            status_map = {item['id']: item['stage'] for item in status_response.get('Items', [])}
            
            enriched_profiles = []
            for process_profile in process_profiles:
                if process_profile.get('profile_id'):
                    # Get full profile data
                    profile_response = self.profiles_table.get_item(
                        Key={'id': process_profile['profile_id']}
                    )
                    if 'Item' in profile_response:
                        profile = profile_response['Item']
                        profile_status = profile.get('status', 1)
                        stage = status_map.get(profile_status, 'Unknown')
                        profile['stage'] = stage
                        enriched_profiles.append(profile)
            return enriched_profiles
        except ClientError:
            return []