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
                FilterExpression='requirement_id = :req_id AND candidate_id = :cand_id',
                ExpressionAttributeValues={
                    ':req_id': profile_data['requirement_id'],
                    ':cand_id': profile_data['candidate_id']
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