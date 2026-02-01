import boto3
import os
from scripts.db.config import AWS_REGION

class LambdaDynamoDBPool:
    _resource = None
    _client = None
    
    @classmethod
    def get_resource(cls):
        if cls._resource is None:
            env = os.getenv('ENVIRONMENT', 'local')
            if env in ['dev', 'prod']:
                # Running in AWS environment
                cls._resource = boto3.resource('dynamodb', region_name=AWS_REGION)
            else:
                # Running locally
                session = boto3.Session(profile_name='developer')
                cls._resource = session.resource('dynamodb', region_name=AWS_REGION)
        return cls._resource
    
    @classmethod
    def get_client(cls):
        if cls._client is None:
            env = os.getenv('ENVIRONMENT', 'local')
            if env in ['dev', 'prod']:
                # Running in AWS environment
                cls._client = boto3.client('dynamodb', region_name=AWS_REGION)
            else:
                # Running locally
                session = boto3.Session(profile_name='developer')
                cls._client = session.client('dynamodb', region_name=AWS_REGION)
        return cls._client

# Global pool instance
pool = LambdaDynamoDBPool()