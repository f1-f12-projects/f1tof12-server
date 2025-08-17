from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from boto3 import client as boto3_client
from os import getenv
from hmac import new as hmac_new
from hashlib import sha256
from base64 import b64encode

router = APIRouter()

def calculate_secret_hash(username: str, client_id: str, client_secret: str):
    message = username + client_id
    dig = hmac_new(client_secret.encode('utf-8'), message.encode('utf-8'), sha256).digest()
    return b64encode(dig).decode()

def get_cognito_config():
    # Try environment variables first
    user_pool_id = getenv('COGNITO_USER_POOL_ID')
    client_id = getenv('COGNITO_CLIENT_ID')
    client_secret = getenv('COGNITO_CLIENT_SECRET')
    
    if user_pool_id and client_id and client_secret:
        return user_pool_id, client_id, client_secret
    
    # Fallback to Parameter Store
    ssm = boto3_client('ssm')
    try:
        user_pool_id = ssm.get_parameter(Name='/f1tof12/cognito/user-pool-id')['Parameter']['Value']
        client_id = ssm.get_parameter(Name='/f1tof12/cognito/client-id')['Parameter']['Value']
        client_secret = ssm.get_parameter(Name='/f1tof12/jwt-secret', WithDecryption=True)['Parameter']['Value']
        return user_pool_id, client_id, client_secret
    except ssm.exceptions.ParameterNotFound as e:
        print(f"SSM Parameter not found: {e}")
        raise HTTPException(status_code=500, detail="Cognito configuration missing")
    except Exception as e:
        print(f"SSM error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Cognito credentials")

def authenticate_with_cognito(username: str, password: str):
    USER_POOL_ID, CLIENT_ID, CLIENT_SECRET = get_cognito_config()
    
    client = boto3_client('cognito-idp', region_name='us-east-1')
    print("Created Cognito client for us-east-1 region")
    
    secret_hash = calculate_secret_hash(username, CLIENT_ID, CLIENT_SECRET)
    print("Calculated SECRET_HASH")
    
    try:
        print("Initiating auth with Cognito")
        response = client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            },
            ClientId=CLIENT_ID
        )
        print("Cognito auth successful")
        return response['AuthenticationResult']['AccessToken']
    except client.exceptions.NotAuthorizedException as e:
        print(f"Cognito auth failed - invalid credentials: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        print(f"Cognito error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cognito error: {str(e)}")

class UserLogin(BaseModel):
    username: str
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Password cannot be empty')
        return v

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=Token)
def login(user: UserLogin):
    print(f"Login request for username: {user.username}")
    cognito_token = authenticate_with_cognito(user.username, user.password)
    print("Login successful, returning token")
    return {"access_token": cognito_token, "token_type": "bearer"}
