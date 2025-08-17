from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from boto3 import client

security = HTTPBearer()

def verify_cognito_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    cognito_client = client('cognito-idp', region_name='us-east-1')
    try:
        response = cognito_client.get_user(AccessToken=credentials.credentials)
        return response['Username']
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Cognito token")