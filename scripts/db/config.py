import os

# SQLite Configuration
DB_FILE_NAME = os.getenv('DB_FILE_NAME', 'f1tof12.db')
DATABASE_URL = f"sqlite:///{DB_FILE_NAME}"

# DynamoDB Configuration
USE_DYNAMODB = os.getenv('USE_DYNAMODB', 'false').lower() == 'true'
AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')
USERS_TABLE = os.getenv('USERS_TABLE', 'f1tof12-users')
COMPANIES_TABLE = os.getenv('COMPANIES_TABLE', 'f1tof12-companies')
SPOCS_TABLE = os.getenv('SPOCS_TABLE', 'f1tof12-spocs')
INVOICES_TABLE = os.getenv('INVOICES_TABLE', 'f1tof12-invoices')