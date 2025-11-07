from fastapi import HTTPException
from boto3 import client as boto3_client
from os import getenv
import logging

logger = logging.getLogger(__name__)

def get_cognito_config():
    """Get Cognito configuration from environment or SSM Parameter Store"""
    from scripts.constants import ENVIRONMENT
    
    # Use environment variables in dev, SSM in production
    if ENVIRONMENT == 'dev':
        user_pool_id = getenv('COGNITO_USER_POOL_ID')
        client_id = getenv('COGNITO_CLIENT_ID')
        client_secret = getenv('COGNITO_CLIENT_SECRET')
        
        if not all([user_pool_id, client_id, client_secret]):
            missing = [k for k, v in {
                'COGNITO_USER_POOL_ID': user_pool_id,
                'COGNITO_CLIENT_ID': client_id, 
                'COGNITO_CLIENT_SECRET': client_secret
            }.items() if not v]
            raise HTTPException(status_code=500, detail=f"Missing env variables: {missing}")
        
        return user_pool_id, client_id, client_secret
    
    # Get customer for multi-tenant support
    customer = getenv('CUSTOMER')
    path_prefix = f'/f1tof12/{ENVIRONMENT}/{customer}'
    
    # Get from Parameter Store (parameters are in us-east-1)
    ssm = boto3_client('ssm', region_name='us-east-1')
    try:
        param_names = [
            f'{path_prefix}/cognito/user-pool-id',
            f'{path_prefix}/cognito/client-id',
            f'{path_prefix}/cognito/client-secret'
        ]
        
        response = ssm.get_parameters(Names=param_names, WithDecryption=True)
        
        params = {p['Name']: p['Value'] for p in response['Parameters']}
        
        # Check if all parameters were found
        missing = [name for name in param_names if name not in params]
        if missing:
            logger.error(f"Missing SSM parameters: {missing}")
            logger.error(f"Found parameters: {list(params.keys())}")
            raise HTTPException(status_code=500, detail=f"Missing SSM parameters: {missing}")
            
        return (
            params[param_names[0]],
            params[param_names[1]],
            params[param_names[2]]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSM Parameter error: {e}")
        raise HTTPException(status_code=500, detail=f"Cognito configuration error: {str(e)}")

def get_cognito_user_pool_id():
    """Get Cognito User Pool ID from configuration"""
    try:
        user_pool_id, _, _ = get_cognito_config()
        return user_pool_id
    except Exception:
        # Fallback to environment variable
        return getenv('COGNITO_USER_POOL_ID')