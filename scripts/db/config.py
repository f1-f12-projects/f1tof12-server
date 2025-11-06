import os

# SQLite Configuration
DB_FILE_NAME = os.getenv('DB_FILE_NAME', 'f1tof12.db')
DATABASE_URL = f"sqlite:///{DB_FILE_NAME}"

# DynamoDB Configuration
USE_DYNAMODB = os.getenv('USE_DYNAMODB', 'false').lower() == 'true'
AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')

# Environment-based table naming
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
TABLE_SUFFIX = '-dev' if ENVIRONMENT == 'dev' else ''

COMPANIES_TABLE = os.getenv('COMPANIES_TABLE', f'f1tof12-companies{TABLE_SUFFIX}')
SPOCS_TABLE = os.getenv('SPOCS_TABLE', f'f1tof12-spocs{TABLE_SUFFIX}')
INVOICES_TABLE = os.getenv('INVOICES_TABLE', f'f1tof12-invoices{TABLE_SUFFIX}')
REQUIREMENTS_TABLE = os.getenv('REQUIREMENTS_TABLE', f'f1tof12-requirements{TABLE_SUFFIX}')
REQUIREMENT_STATUSES_TABLE = os.getenv('REQUIREMENT_STATUSES_TABLE', f'f1tof12-requirement-statuses{TABLE_SUFFIX}')
PROFILE_STATUSES_TABLE = os.getenv('PROFILE_STATUSES_TABLE', f'f1tof12-profile-statuses{TABLE_SUFFIX}')
COUNTERS_TABLE = os.getenv('COUNTERS_TABLE', f'f1tof12-counters{TABLE_SUFFIX}')
PROFILES_TABLE = os.getenv('PROFILES_TABLE', f'f1tof12-profiles{TABLE_SUFFIX}')
PROCESS_PROFILES_TABLE = os.getenv('PROCESS_PROFILES_TABLE', f'f1tof12-process-profiles{TABLE_SUFFIX}')
LEAVES_TABLE = os.getenv('LEAVES_TABLE', f'f1tof12-leaves{TABLE_SUFFIX}')
LEAVE_BALANCES_TABLE = os.getenv('LEAVE_BALANCES_TABLE', f'f1tof12-leave-balances{TABLE_SUFFIX}')