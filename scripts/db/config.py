import os

DB_FILE_NAME = os.getenv('DB_FILE_NAME', 'f1tof12.db')
# Use /tmp for Lambda, current directory for local
if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
    TMP_DB_PATH = os.path.join('/tmp', DB_FILE_NAME)
else:
    TMP_DB_PATH = DB_FILE_NAME
DATABASE_URL = f"sqlite:///{TMP_DB_PATH}"
S3_BUCKET = os.getenv('S3_BUCKET', 'f1tof12-db-backup')