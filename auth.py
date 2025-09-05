from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import boto3
from functools import wraps
from typing import List, Optional
from scripts.constants import AWS_REGION, ALLOWED_ROLES, DEFAULT_ROLE, ROLES, FINANCE_ROLE, LEAD_ROLE, MANAGER_ROLE, RECRUITER_ROLE
security = HTTPBearer()

def get_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)
    try:
        response = cognito_client.get_user(AccessToken=credentials.credentials)
        # Extract role from custom attributes
        role = None
        for attr in response.get('UserAttributes', []):
            if attr['Name'] == 'custom:role':
                role = attr['Value']
                break
        return {
            'username': response['Username'],
            'role': role or DEFAULT_ROLE,  # Default role
            'attributes': response.get('UserAttributes', [])
        }
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Cognito token")

def verify_cognito_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_info = get_user_info(credentials)
    return user_info['username']

def require_roles(allowed_roles: List[str]):
    def decorator(credentials: HTTPAuthorizationCredentials = Depends(security)):
        user_info = get_user_info(credentials)
        if user_info['role'] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        return user_info
    return decorator

# Business role dependencies
def require_finance(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return require_roles([ROLES[FINANCE_ROLE]])(credentials)

def require_lead(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return require_roles([ROLES[LEAD_ROLE]])(credentials)

def require_manager(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return require_roles([ROLES[MANAGER_ROLE]])(credentials)

def require_recruiter(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return require_roles([ROLES[RECRUITER_ROLE]])(credentials)

# Admin role dependency (all roles)
def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return require_roles(ALLOWED_ROLES)(credentials)

# Alias for admin
require_management = require_admin

# Combined role dependencies
def require_lead_or_recruiter(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return require_roles([ROLES[LEAD_ROLE], ROLES[RECRUITER_ROLE]])(credentials)