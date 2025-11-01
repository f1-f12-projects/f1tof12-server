import boto3
from scripts.db.config import AWS_REGION

class LambdaDynamoDBPool:
    _resource = None
    _client = None
    
    @classmethod
    def get_resource(cls):
        if cls._resource is None:
            cls._resource = boto3.resource('dynamodb', region_name=AWS_REGION)
        return cls._resource
    
    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = boto3.client('dynamodb', region_name=AWS_REGION)
        return cls._client

# Global pool instance
pool = LambdaDynamoDBPool()