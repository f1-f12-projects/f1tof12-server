from fastapi import HTTPException
from botocore.exceptions import ClientError
import logging
from . import logging_config

logger = logging.getLogger(__name__)

def success_response(data=None, message="Success"):
    """Standard success response format"""
    response = {"success": True, "message": message}
    if data is not None:
        response["data"] = data
    return response

def handle_error(e: Exception, operation: str = "operation"):
    """Handle exceptions and return appropriate HTTPException"""
    if isinstance(e, ClientError):
        error_info = e.response.get('Error', {})
        error_code = error_info.get('Code', 'UnknownError')
        error_message = error_info.get('Message', str(e))
        
        error_mappings = {
            'UserNotFoundException': (404, "USER_NOT_FOUND", "User not found"),
            'NotAuthorizedException': (401, "UNAUTHORIZED", "Invalid credentials"),
            'InvalidParameterException': (400, "INVALID_PARAMETER", error_message),
            'UsernameExistsException': (409, "USER_EXISTS", "User already exists"),
            'InvalidPasswordException': (400, "INVALID_PASSWORD", error_message),
            'UserNotConfirmedException': (400, "USER_NOT_CONFIRMED", "User not confirmed"),
            'TooManyRequestsException': (429, "TOO_MANY_REQUESTS", "Too many requests"),
            'PasswordResetRequiredException': (400, "PASSWORD_CHANGE_REQUIRED", "Password change required")
        }
        
        if error_code in error_mappings:
            status_code, error_type, message = error_mappings[error_code]
            raise HTTPException(status_code=status_code, detail={
                "error": error_type,
                "message": message,
                "code": error_code
            })
    
    logger.error(f"{operation} failed: {str(e)}")
    raise HTTPException(status_code=500, detail={
        "error": "INTERNAL_ERROR",
        "message": f"Failed to {operation}",
        "code": "INTERNAL_500"
    })
