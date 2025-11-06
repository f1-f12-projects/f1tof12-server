from os import getenv
from scripts.utils.cognito import get_cognito_user_pool_id

# AWS Cognito Configuration
COGNITO_USER_POOL_ID = get_cognito_user_pool_id()

# Role Constants
FINANCE_ROLE = 'finance'
LEAD_ROLE = 'lead'
MANAGER_ROLE = 'manager'
RECRUITER_ROLE = 'recruiter'
HR_ROLE = 'hr'

# Role Map
ROLES = {
    FINANCE_ROLE: FINANCE_ROLE,
    LEAD_ROLE: LEAD_ROLE,
    MANAGER_ROLE: MANAGER_ROLE,
    RECRUITER_ROLE: RECRUITER_ROLE,
    HR_ROLE: HR_ROLE
}

# User Roles
ALLOWED_ROLES = [FINANCE_ROLE, LEAD_ROLE, MANAGER_ROLE, RECRUITER_ROLE, HR_ROLE]
DEFAULT_ROLE = RECRUITER_ROLE

# Environment Configuration
ENVIRONMENT = getenv('ENVIRONMENT', 'dev')

# AWS Configuration
AWS_REGION = 'us-east-1'

# Status Values
USER_STATUS_ACTIVE = 'active'
USER_STATUS_INACTIVE = 'inactive'
# Leave Constants
LEAVE_TYPES = ['annual', 'sick', 'casual']
LEAVE_STATUS = ['pending', 'approved', 'rejected']