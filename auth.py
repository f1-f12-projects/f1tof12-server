from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import boto3
from typing import List
from scripts.constants import AWS_REGION, DEFAULT_ROLE, ROLES, FINANCE_ROLE, LEAD_ROLE, MANAGER_ROLE, RECRUITER_ROLE

security = HTTPBearer()
cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)

def get_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        response = cognito_client.get_user(AccessToken=credentials.credentials)
        # Extract role from custom attributes
        role = None
        for attr in response.get('UserAttributes', []):
            if attr['Name'] == 'custom:role':
                role = attr['Value']
                break
        
        user_info = {
            'username': response['Username'],
            'role': role or DEFAULT_ROLE,
            'attributes': response.get('UserAttributes', [])
        }

        return user_info
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Cognito token")

def verify_cognito_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_info = get_user_info(credentials)
    return user_info['username']

def require_roles(allowed_roles: List[str]):
    def decorator(credentials: HTTPAuthorizationCredentials = Depends(security)):
        user_info = get_user_info(credentials)
        user_role = user_info['role']
        
        # Manager role has access to all other roles
        if user_role == ROLES[MANAGER_ROLE]:
            return user_info
            
        # Lead role has recruiter permissions
        if user_role == ROLES[LEAD_ROLE] and ROLES[RECRUITER_ROLE] in allowed_roles:
            return user_info
            
        # Check if user role is in allowed roles
        if user_role in allowed_roles:
            return user_info

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Access denied. Required roles: {allowed_roles}"
        )
    return decorator

# Business role dependencies
require_finance = require_roles([ROLES[FINANCE_ROLE]])
require_lead = require_roles([ROLES[LEAD_ROLE]])
require_manager = require_roles([ROLES[MANAGER_ROLE]])
require_recruiter = require_roles([ROLES[RECRUITER_ROLE]])

# Aliases
require_admin = require_manager
require_management = require_manager

# Combined role dependencies
require_lead_or_recruiter = require_roles([ROLES[LEAD_ROLE], ROLES[RECRUITER_ROLE]])
require_finance_or_manager = require_roles([ROLES[FINANCE_ROLE], ROLES[MANAGER_ROLE]])