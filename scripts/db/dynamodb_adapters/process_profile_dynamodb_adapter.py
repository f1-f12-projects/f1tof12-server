from typing import Dict, Any
from botocore.exceptions import ClientError
from scripts.db.config import PROCESS_PROFILES_TABLE
from .base_dynamodb_adapter import BaseDynamoDBAdapter

class ProcessProfileDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.process_profiles_table = self.dynamodb.Table(PROCESS_PROFILES_TABLE)
    
    def create_process_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
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
        
        profile_id = self._get_next_id('process_profiles')
        profile_data['id'] = profile_id
        self.process_profiles_table.put_item(Item=profile_data)
        return profile_data
    
    def upsert_process_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = self.process_profiles_table.scan(
                FilterExpression='requirement_id = :req_id AND profile_id = :prof_id',
                ExpressionAttributeValues={
                    ':req_id': profile_data['requirement_id'],
                    ':prof_id': profile_data['profile_id']
                }
            )
            
            if response.get('Items'):
                existing = response['Items'][0]
                self.process_profiles_table.put_item(Item={**existing, **profile_data})
                return {**existing, **profile_data}
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
                FilterExpression='requirement_id = :req_id',
                ExpressionAttributeValues={
                    ':req_id': requirement_id
                }
            )
            return response.get('Items', [])
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
            return response.get('Items', [])
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
    
    def update_process_profile_status(self, requirement_id: int, profile_id: int, status: int) -> bool:
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
                    Item={**item, 'status': status}
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