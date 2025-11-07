from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, field_validator
from boto3 import client as boto3_client
from os import getenv
from hmac import new as hmac_new
from hashlib import sha256
from base64 import b64encode
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from auth import require_admin, require_user_management, require_hr_or_lead
from typing import Optional
from scripts.utils.response import success_response, handle_error
from scripts.utils.cognito import get_cognito_config
from scripts.constants import AWS_REGION, ALLOWED_ROLES, DEFAULT_ROLE
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

router = APIRouter()

def calculate_secret_hash(username: str, client_id: str, client_secret: str):
    message = username + client_id
    dig = hmac_new(client_secret.encode('utf-8'), message.encode('utf-8'), sha256).digest()
    return b64encode(dig).decode()

def authenticate_with_cognito(username: str, password: str):
    USER_POOL_ID, CLIENT_ID, CLIENT_SECRET = get_cognito_config()
    if not USER_POOL_ID or not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Failed to authenticate. Please check the server configuration.")
    
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    
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
            raise HTTPException(status_code=400, detail={
                "error": "PASSWORD_CHANGE_REQUIRED",
                "message": "Password change required",
                "code": "PASSWORD_CHANGE_REQUIRED_400"
            })
        
        logger.info("Auth successful")
        return response['AuthenticationResult']
    except client.exceptions.NotAuthorizedException as e:
        error_msg = str(e)
        if "User is disabled" in error_msg:
            logger.warning(f"Auth failed - user disabled: {username}")
            raise HTTPException(status_code=403, detail={
                "error": "USER_DISABLED",
                "message": "User account is disabled",
                "code": "USER_DISABLED_403"
            })
        logger.warning(f"Auth failed - invalid credentials: {e}")
        raise HTTPException(status_code=401, detail={
            "error": "INVALID_CREDENTIALS",
            "message": "Invalid credentials",
            "code": "INVALID_CREDENTIALS_401"
        })
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
    role: Optional[str] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v is not None and v not in ALLOWED_ROLES:
            raise ValueError(f'Role must be one of: {ALLOWED_ROLES}')
        return v

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

@router.post("/login", status_code=status.HTTP_200_OK)
def login(user: UserLogin):
    logger.info(f"[ENTRY] Login API called for username: {user.username}")
    try:
        # Use Cognito authentication
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
        
        logger.info(f"[EXIT] Login API successful for username: {user.username}")
        return success_response({
            "access_token": auth_result['AccessToken'],
            "refresh_token": auth_result['RefreshToken'],
            "token_type": "bearer",
            "role": role
        }, "Login successful")
    except HTTPException as e:
        logger.error(f"[ERROR] Login API failed for {user.username}: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"[ERROR] Login API failed for {user.username}: {str(e)}")
        handle_error(e, "login")

@router.post("/refresh-token")
def refresh_token(refresh_data: RefreshToken):
    logger.info("[ENTRY] Refresh token API called")
    _, CLIENT_ID, CLIENT_SECRET = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)

    if CLIENT_ID is None or CLIENT_SECRET is None:
        logger.error("[ERROR] Refresh token API failed: Cognito configuration not set")
        raise HTTPException(status_code=500, detail="Token is not refreshed. Please check the server configuration.")
    
    try:
        response = client.initiate_auth(
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_data.refresh_token,
                'SECRET_HASH': calculate_secret_hash('', CLIENT_ID, CLIENT_SECRET)
            },
            ClientId=CLIENT_ID
        )

        logger.info("[EXIT] Refresh token API successful")
        return success_response({
            "access_token": response['AuthenticationResult']['AccessToken'],
            "token_type": "bearer"
        }, "Token refreshed successfully")
    except Exception as e:
        logger.error(f"[ERROR] Refresh token API failed: {str(e)}")
        handle_error(e, "refresh token")

@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    logger.info("[ENTRY] Logout API called")
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    try:
        client.global_sign_out(AccessToken=credentials.credentials)
        logger.info("User logged out")
    except client.exceptions.NotAuthorizedException:
        logger.info("Token already invalid or expired")
    except Exception as e:
        logger.warning(f"Logout failed: {str(e)}")
    logger.info("[EXIT] Logout API completed")
    return success_response(message="Logged out successfully")

@router.get("/users")
def get_cognito_users(user_info: dict = Depends(require_hr_or_lead)):
    logger.info("[ENTRY] Get users API called")
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
        logger.error(f"[ERROR] Get users API failed: {str(e)}")
        handle_error(e, "fetch users")

@router.get("/user/{username}")
def get_user_details(username: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    logger.info(f"[ENTRY] Get user details API called for: {username}")
    
    try:
        client = boto3_client('cognito-idp', region_name=AWS_REGION)
        
        response = client.get_user(AccessToken=credentials.credentials)
        
        # Only allow users to fetch their own details
        if response['Username'].lower() != username.lower():
            raise HTTPException(status_code=403, detail={"error": "ACCESS_DENIED", "message": "Can only access your own details", "code": "USER_403"})
        
        def get_attr(attributes, name):
            return next((attr['Value'] for attr in attributes if attr['Name'] == name), None)
        
        user_details = {
            "username": response['Username'],
            "email": get_attr(response['UserAttributes'], 'email'),
            "phone_number": get_attr(response['UserAttributes'], 'phone_number'),
            "given_name": get_attr(response['UserAttributes'], 'given_name'),
            "family_name": get_attr(response['UserAttributes'], 'family_name'),
            "role": get_attr(response['UserAttributes'], 'custom:role') or DEFAULT_ROLE
        }
        
        logger.info(f"[EXIT] Get user details API successful for: {username}")
        return success_response(user_details, "User details retrieved successfully")
    except client.exceptions.NotAuthorizedException:
        logger.error("[ERROR] Invalid or expired token")
        raise HTTPException(status_code=401, detail={"error": "INVALID_TOKEN", "message": "Invalid or expired token", "code": "USER_401"})
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Get user details API failed for {username}: {str(e)}")
        handle_error(e, "fetch user details")

@router.put("/user/{target_username}/update")
def update_user(target_username: str, user_update: UserUpdate, user_info: dict = Depends(require_user_management)):
    logger.info(f"[ENTRY] Update user API called for: {target_username}")
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
        if user_update.role:
            attributes.append({'Name': 'custom:role', 'Value': user_update.role})
        
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
        
        logger.info(f"[EXIT] Update user API successful for: {target_username}")
        return success_response(message=f"User {target_username} updated successfully")
    except Exception as e:
        logger.error(f"[ERROR] Update user API failed for {target_username}: {str(e)}")
        handle_error(e, "update user")

@router.post("/user/{target_username}/enable")
def enable_user(target_username: str, user_info: dict = Depends(require_user_management)):
    logger.info(f"[ENTRY] Enable user API called for: {target_username}")
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    try:
        client.admin_enable_user(UserPoolId=USER_POOL_ID, Username=target_username)
        logger.info(f"[EXIT] Enable user API successful for: {target_username}")
        return success_response(message=f"User {target_username} enabled successfully")
    except Exception as e:
        logger.error(f"[ERROR] Enable user API failed for {target_username}: {str(e)}")
        handle_error(e, "enable user")

@router.post("/user/{target_username}/disable")
def disable_user(target_username: str, user_info: dict = Depends(require_user_management)):
    logger.info(f"[ENTRY] Disable user API called for: {target_username}")
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    try:
        client.admin_disable_user(UserPoolId=USER_POOL_ID, Username=target_username)
        logger.info(f"[EXIT] Disable user API successful for: {target_username}")
        return success_response(message=f"User {target_username} disabled successfully")
    except Exception as e:
        logger.error(f"[ERROR] Disable user API failed for {target_username}: {str(e)}")
        handle_error(e, "disable user")

@router.post("/user/create")
def create_user(user_data: UserCreate, user_info: dict = Depends(require_admin)):
    logger.info(f"[ENTRY] Create user API called for: {user_data.username}")
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
        logger.info(f"Setting role for user {user_data.username}: {role}")
        attributes.append({'Name': 'custom:role', 'Value': role})
        
        client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=user_data.username,
            UserAttributes=attributes,
            TemporaryPassword=user_data.temporary_password,
            MessageAction='SUPPRESS'
        )
        logger.info(f"[EXIT] Create user API successful for: {user_data.username}")
        return success_response(message=f"User {user_data.username} created successfully")
    except Exception as e:
        logger.error(f"[ERROR] Create user API failed for {user_data.username}: {str(e)}")
        handle_error(e, "create user")

@router.post("/user/{target_username}/reset-password")
def reset_password(target_username: str, password_data: PasswordReset, user_info: dict = Depends(require_user_management)):
    logger.info(f"[ENTRY] Reset password API called for: {target_username}")
    USER_POOL_ID, _, _ = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)
    
    try:
        client.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=target_username,
            Password=password_data.new_temporary_password,
            Permanent=False
        )
        logger.info(f"[EXIT] Reset password API successful for: {target_username}")
        return success_response(message=f"Temporary password reset for user {target_username}")
    except Exception as e:
        logger.error(f"[ERROR] Reset password API failed for {target_username}: {str(e)}")
        handle_error(e, "reset password")

@router.post("/user/change-password")
def change_password(password_data: PasswordChange):
    logger.info(f"[ENTRY] Change password API called for username: {password_data.username}")
    
    _, CLIENT_ID, CLIENT_SECRET = get_cognito_config()
    client = boto3_client('cognito-idp', region_name=AWS_REGION)

    if CLIENT_ID is None or CLIENT_SECRET is None:
        logger.error("[ERROR] Refresh token API failed: Cognito configuration not set")
        raise HTTPException(status_code=500, detail="Token is not refreshed. Please check the server configuration.")
    
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
            logger.info(f"[EXIT] Change password API successful for user: {password_data.username}")
            return success_response(message="Password changed successfully")
        else:
            logger.warning(f"Password change not required for user: {password_data.username}.")
            raise HTTPException(status_code=400, detail={
                "error": "PASSWORD_CHANGE_NOT_REQUIRED",
                "message": "Password change not required",
                "code": "PWD_400"
            })
    except HTTPException as e:
        logger.error(f"[ERROR] Change password API failed for {password_data.username}: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"[ERROR] Change password API failed for {password_data.username}: {str(e)}")
        handle_error(e, "change password")


