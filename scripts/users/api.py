from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, field_validator
from boto3 import client as boto3_client
from os import getenv
from hmac import new as hmac_new
from hashlib import sha256
from base64 import b64encode
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from auth import verify_cognito_token, AWS_REGION
from typing import Optional

security = HTTPBearer()

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
        client_secret = ssm.get_parameter(Name='/f1tof12/cognito/client-secret', WithDecryption=True)['Parameter']['Value']
        return user_pool_id, client_id, client_secret
    except ssm.exceptions.ParameterNotFound as e:
        print(f"SSM Parameter not found: {e}")
        raise HTTPException(status_code=500, detail="Cognito configuration missing")
    except Exception as e:
        print(f"SSM error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Cognito credentials")

def authenticate_with_cognito(username: str, password: str):
    USER_POOL_ID, CLIENT_ID, CLIENT_SECRET = get_cognito_config()
    
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    print(f"Created Cognito client for {AWS_REGION} region")
    
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
        return response['AuthenticationResult']
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
    refresh_token: str
    token_type: str
    status_code: int

class RefreshToken(BaseModel):
    refresh_token: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    phone_number: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    status: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    temporary_password: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    phone_number: Optional[str] = None

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(user: UserLogin):
    print(f"Login request for username: {user.username}")
    auth_result = authenticate_with_cognito(user.username, user.password)
    print("Login successful, returning tokens")
    return {
        "access_token": auth_result['AccessToken'],
        "refresh_token": auth_result['RefreshToken'],
        "token_type": "bearer",
        "status_code": 200
    }

@router.post("/refresh")
def refresh_token(refresh_data: RefreshToken):
    _, CLIENT_ID, CLIENT_SECRET = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    
    try:
        response = client.initiate_auth(
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_data.refresh_token,
                'SECRET_HASH': calculate_secret_hash('', CLIENT_ID, CLIENT_SECRET)
            },
            ClientId=CLIENT_ID
        )
        return {
            "access_token": response['AuthenticationResult']['AccessToken'],
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    try:
        client.global_sign_out(AccessToken=credentials.credentials)
    except Exception:
        pass  # Token may already be invalid
    return {"message": "Logged out successfully"}

@router.get("/users")
def get_cognito_users(username: str = Depends(verify_cognito_token)):
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    try:
        response = client.list_users(UserPoolId=USER_POOL_ID)
        users = [{
            "username": user['Username'],
            "email": next((attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'email'), None),
            "phone_number": next((attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'phone_number'), None),
            "given_name": next((attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'given_name'), None),
            "family_name": next((attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'family_name'), None),
            "status": user['UserStatus'],
            "created": user['UserCreateDate'].isoformat(),
            "enabled": user['Enabled']
        } for user in response['Users']]
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")

@router.put("/user/{target_username}/update")
def update_user(target_username: str, user_update: UserUpdate, username: str = Depends(verify_cognito_token)):
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    
    try:
        # Update user attributes
        attributes = []
        if user_update.email:
            attributes.append({'Name': 'email', 'Value': user_update.email})
        if user_update.phone_number:
            attributes.append({'Name': 'phone_number', 'Value': user_update.phone_number})
        if user_update.given_name:
            attributes.append({'Name': 'given_name', 'Value': user_update.given_name})
        if user_update.family_name:
            attributes.append({'Name': 'family_name', 'Value': user_update.family_name})
        
        if attributes:
            client.admin_update_user_attributes(
                UserPoolId=USER_POOL_ID,
                Username=target_username,
                UserAttributes=attributes
            )
        
        # Update user status if provided
        if user_update.status:
            if user_update.status.upper() == 'FORCE_CHANGE_PASSWORD':
                client.admin_set_user_password(
                    UserPoolId=USER_POOL_ID,
                    Username=target_username,
                    Temporary=True
                )
            elif user_update.status.upper() == 'CONFIRMED':
                client.admin_confirm_sign_up(
                    UserPoolId=USER_POOL_ID,
                    Username=target_username
                )
        
        return {"message": f"User {target_username} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

@router.post("/user/{target_username}/enable")
def enable_user(target_username: str, username: str = Depends(verify_cognito_token)):
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    try:
        client.admin_enable_user(UserPoolId=USER_POOL_ID, Username=target_username)
        return {"message": f"User {target_username} enabled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable user: {str(e)}")

@router.post("/user/{target_username}/disable")
def disable_user(target_username: str, username: str = Depends(verify_cognito_token)):
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    try:
        client.admin_disable_user(UserPoolId=USER_POOL_ID, Username=target_username)
        return {"message": f"User {target_username} disabled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable user: {str(e)}")

@router.post("/user/create")
def create_user(user_data: UserCreate, username: str = Depends(verify_cognito_token)):
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    
    try:
        attributes = [{'Name': 'email', 'Value': user_data.email}]
        if user_data.given_name:
            attributes.append({'Name': 'given_name', 'Value': user_data.given_name})
        if user_data.family_name:
            attributes.append({'Name': 'family_name', 'Value': user_data.family_name})
        if user_data.phone_number:
            attributes.append({'Name': 'phone_number', 'Value': user_data.phone_number})
        
        client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=user_data.username,
            UserAttributes=attributes,
            TemporaryPassword=user_data.temporary_password,
            MessageAction='SUPPRESS'
        )
        return {"message": f"User {user_data.username} created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
