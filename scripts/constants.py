# Role Constants
FINANCE_ROLE = 'finance'
LEAD_ROLE = 'lead'
MANAGER_ROLE = 'manager'
RECRUITER_ROLE = 'recruiter'

# Role Map
ROLES = {
    FINANCE_ROLE: FINANCE_ROLE,
    LEAD_ROLE: LEAD_ROLE,
    MANAGER_ROLE: MANAGER_ROLE,
    RECRUITER_ROLE: RECRUITER_ROLE
}

# User Roles
ALLOWED_ROLES = [FINANCE_ROLE, LEAD_ROLE, MANAGER_ROLE, RECRUITER_ROLE]
DEFAULT_ROLE = RECRUITER_ROLE

# Environment Configuration
from os import getenv
ENVIRONMENT = getenv('ENVIRONMENT', 'dev')

# AWS Configuration
AWS_REGION = 'us-east-1'

# Status Values
USER_STATUS_ACTIVE = 'active'
USER_STATUS_INACTIVE = 'inactive'