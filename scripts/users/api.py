from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
import os
import hmac
import hashlib
import base64

router = APIRouter()

def calculate_secret_hash(username: str, client_id: str, client_secret: str):
    message = username + client_id
    dig = hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

def authenticate_with_cognito(username: str, password: str):
    print(f"Starting Cognito auth for user: {username}")
    
    USER_POOL_ID = 'us-east-1_xyI1bndIE'
    CLIENT_ID = '8oh3qa5irejj7hhe4ldn751h9'
    CLIENT_SECRET = '1pf9r2dcedlibiq4rgev4k02nansg0jr60mpbeg5hg4ur9g0uppb'
    
    print(f"USER_POOL_ID: {USER_POOL_ID}")
    print(f"CLIENT_ID: {CLIENT_ID}")
    
    if not USER_POOL_ID or not CLIENT_ID or not CLIENT_SECRET:
        print("Cognito credentials not configured")
        raise HTTPException(status_code=500, detail="Cognito not configured")
    
    client = boto3.client('cognito-idp', region_name='us-east-1')
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
        print(f"Authentication result: {response}")
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

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=Token)
def login(user: UserLogin):
    print(f"Login request for username: {user.username}")
    cognito_token = authenticate_with_cognito(user.username, user.password)
    print("Login successful, returning token")
    return {"access_token": cognito_token, "token_type": "bearer"}
