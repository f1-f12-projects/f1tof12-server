from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, field_validator
from boto3 import client as boto3_client
from os import getenv
from hmac import new as hmac_new
from hashlib import sha256
from base64 import b64encode
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from auth import verify_cognito_token, require_admin, require_manager
from typing import Optional
from scripts.utils.response import success_response, handle_error
from scripts.constants import AWS_REGION, ALLOWED_ROLES, DEFAULT_ROLE
import logging

logger = logging.getLogger(__name__)

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
        response = ssm.get_parameters(
            Names=['/f1tof12/cognito/user-pool-id', '/f1tof12/cognito/client-id', '/f1tof12/cognito/client-secret'],
            WithDecryption=True
        )
        params = {p['Name']: p['Value'] for p in response['Parameters']}
        return params['/f1tof12/cognito/user-pool-id'], params['/f1tof12/cognito/client-id'], params['/f1tof12/cognito/client-secret']
    except ssm.exceptions.ParameterNotFound as e:
        logger.error(f"SSM Parameter not found: {e}")
        raise HTTPException(status_code=500, detail="Cognito configuration missing")
    except Exception as e:
        logger.error(f"SSM error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Cognito credentials")

def authenticate_with_cognito(username: str, password: str):
    USER_POOL_ID, CLIENT_ID, CLIENT_SECRET = get_cognito_config()
    
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    logger.debug(f"Created client for {AWS_REGION} region")
    
    secret_hash = calculate_secret_hash(username, CLIENT_ID, CLIENT_SECRET)
    
    try:
        logger.info("Initiating auth")
        response = client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            },
            ClientId=CLIENT_ID
        )
        
        # Check if password change is required
        if 'ChallengeName' in response and response['ChallengeName'] == 'NEW_PASSWORD_REQUIRED':
            raise HTTPException(status_code=400, detail="Password change required.")
        
        logger.info("Auth successful")
        return response['AuthenticationResult']
    except client.exceptions.NotAuthorizedException as e:
        logger.warning(f"Auth failed - invalid credentials: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error while authenticating: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while authenticating: {str(e)}")

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
    role: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    phone_number: Optional[str] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v is not None:
            if v not in ALLOWED_ROLES:
                raise ValueError(f'Role must be one of: {ALLOWED_ROLES}')
        return v

class PasswordReset(BaseModel):
    new_temporary_password: str

class PasswordChange(BaseModel):
    username: str
    temporary_password: str
    new_password: str

class RoleAssignment(BaseModel):
    role: str
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ALLOWED_ROLES:
            raise ValueError(f'Role must be one of: {ALLOWED_ROLES}')
        return v

@router.post("/login", status_code=status.HTTP_200_OK)
def login(user: UserLogin):
    logger.info(f"Login request for username: {user.username}")
    auth_result = authenticate_with_cognito(user.username, user.password)
    
    # Get user role from Cognito
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    try:
        user_response = client.get_user(AccessToken=auth_result['AccessToken'])
        role = DEFAULT_ROLE
        for attr in user_response.get('UserAttributes', []):
            if attr['Name'] == 'custom:role':
                role = attr['Value']
                break
    except Exception:
        role = DEFAULT_ROLE
    
    return success_response({
        "access_token": auth_result['AccessToken'],
        "refresh_token": auth_result['RefreshToken'],
        "token_type": "bearer",
        "role": role
    }, "Login successful")

@router.post("/refresh-token")
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
        return success_response({
            "access_token": response['AuthenticationResult']['AccessToken'],
            "token_type": "bearer"
        }, "Token refreshed successfully")
    except Exception as e:
        handle_error(e, "refresh token")

@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    try:
        client.global_sign_out(AccessToken=credentials.credentials)
    except client.exceptions.NotAuthorizedException:
        logger.info("Token already invalid or expired")
    except Exception as e:
        logger.warning(f"Logout failed: {str(e)}")
    return success_response(message="Logged out successfully")

@router.get("/users")
def get_cognito_users(user_info: dict = Depends(require_manager)):
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    try:
        response = client.list_users(UserPoolId=USER_POOL_ID)
        def get_attr(attributes, name):
            return next((attr['Value'] for attr in attributes if attr['Name'] == name), None)
        
        users = [{
            "username": user['Username'],
            "email": get_attr(user['Attributes'], 'email'),
            "phone_number": get_attr(user['Attributes'], 'phone_number'),
            "given_name": get_attr(user['Attributes'], 'given_name'),
            "family_name": get_attr(user['Attributes'], 'family_name'),
            "role": get_attr(user['Attributes'], 'custom:role') or DEFAULT_ROLE,
            "status": user['UserStatus'],
            "created": user['UserCreateDate'].isoformat(),
            "enabled": user['Enabled']
        } for user in response['Users']]
        return success_response(users, "Users retrieved successfully")
    except Exception as e:
        handle_error(e, "fetch users")

@router.put("/user/{target_username}/update")
def update_user(target_username: str, user_update: UserUpdate, user_info: dict = Depends(require_admin)):
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
                client.admin_reset_user_password(
                    UserPoolId=USER_POOL_ID,
                    Username=target_username
                )
            elif user_update.status.upper() == 'CONFIRMED':
                client.admin_confirm_sign_up(
                    UserPoolId=USER_POOL_ID,
                    Username=target_username
                )
        
        return success_response(message=f"User {target_username} updated successfully")
    except Exception as e:
        handle_error(e, "update user")

@router.post("/user/{target_username}/enable")
def enable_user(target_username: str, user_info: dict = Depends(require_admin)):
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    try:
        client.admin_enable_user(UserPoolId=USER_POOL_ID, Username=target_username)
        return success_response(message=f"User {target_username} enabled successfully")
    except Exception as e:
        handle_error(e, "enable user")

@router.post("/user/{target_username}/disable")
def disable_user(target_username: str, user_info: dict = Depends(require_admin)):
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    try:
        client.admin_disable_user(UserPoolId=USER_POOL_ID, Username=target_username)
        return success_response(message=f"User {target_username} disabled successfully")
    except Exception as e:
        handle_error(e, "disable user")

@router.post("/user/create")
def create_user(user_data: UserCreate, user_info: dict = Depends(require_admin)):
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
        # Set role (default to recruiter if not provided)
        role = user_data.role or DEFAULT_ROLE
        attributes.append({'Name': 'custom:role', 'Value': role})
        
        client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=user_data.username,
            UserAttributes=attributes,
            TemporaryPassword=user_data.temporary_password,
            MessageAction='SUPPRESS'
        )
        return success_response(message=f"User {user_data.username} created successfully")
    except Exception as e:
        handle_error(e, "create user")

@router.post("/user/{target_username}/reset-password")
def reset_password(target_username: str, password_data: PasswordReset, user_info: dict = Depends(require_admin)):
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    
    try:
        client.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=target_username,
            Password=password_data.new_temporary_password,
            Permanent=False
        )
        return success_response(message=f"Temporary password reset for user {target_username}")
    except Exception as e:
        handle_error(e, "reset password")

@router.post("/user/change-password")
def change_password(password_data: PasswordChange):
    _, CLIENT_ID, CLIENT_SECRET = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    
    secret_hash = calculate_secret_hash(password_data.username, CLIENT_ID, CLIENT_SECRET)
    
    try:
        # First authenticate with temporary password
        auth_response = client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': password_data.username,
                'PASSWORD': password_data.temporary_password,
                'SECRET_HASH': secret_hash
            },
            ClientId=CLIENT_ID
        )
        
        # Handle NEW_PASSWORD_REQUIRED challenge
        if 'ChallengeName' in auth_response and auth_response['ChallengeName'] == 'NEW_PASSWORD_REQUIRED':
            client.respond_to_auth_challenge(
                ClientId=CLIENT_ID,
                ChallengeName='NEW_PASSWORD_REQUIRED',
                Session=auth_response['Session'],
                ChallengeResponses={
                    'USERNAME': password_data.username,
                    'NEW_PASSWORD': password_data.new_password,
                    'SECRET_HASH': secret_hash
                }
            )
            return success_response(message="Password changed successfully")
        else:
            raise HTTPException(status_code=400, detail={
                "error": "PASSWORD_CHANGE_NOT_REQUIRED",
                "message": "Password change not required",
                "code": "PWD_400"
            })
    except Exception as e:
        handle_error(e, "change password")

@router.post("/user/{target_username}/assign-role")
def assign_role(target_username: str, role_data: RoleAssignment, user_info: dict = Depends(require_admin)):
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    
    try:
        client.admin_update_user_attributes(
            UserPoolId=USER_POOL_ID,
            Username=target_username,
            UserAttributes=[
                {'Name': 'custom:role', 'Value': role_data.role}
            ]
        )
        return success_response(message=f"Role '{role_data.role}' assigned to user {target_username}")
    except Exception as e:
        handle_error(e, "assign role")

@router.get("/user/{target_username}/role")
def get_user_role(target_username: str, user_info: dict = Depends(require_manager)):
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    
    try:
        response = client.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=target_username
        )
        
        role = DEFAULT_ROLE  # Default role
        for attr in response['UserAttributes']:
            if attr['Name'] == 'custom:role':
                role = attr['Value']
                break
        
        return success_response({'username': target_username, 'role': role}, "User role retrieved successfully")
    except Exception as e:
        handle_error(e, "get user role")
