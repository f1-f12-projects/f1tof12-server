import boto3
import os
import logging

logger = logging.getLogger(__name__)

# AWS S3 integration
s3_client = boto3.client('s3')
S3_BUCKET = os.getenv('S3_BUCKET', 'f1tof12-db-backup')
DB_FILE_NAME = 'f1tof12.db'
DB_FILE = '/tmp/' + DB_FILE_NAME

def backup_to_s3():
    """Upload SQLite database to S3"""
    try:
        s3_client.upload_file(DB_FILE, S3_BUCKET, DB_FILE_NAME)
        logger.info(f"S3 backup completed successfully: {DB_FILE_NAME}")
        return True
    except Exception as e:
        logger.error(f"S3 backup failed: {e}")
        return False

def restore_from_s3():
    """Download SQLite database from S3"""
    try:
        s3_client.download_file(S3_BUCKET, DB_FILE_NAME, DB_FILE)
        logger.info(f"S3 restore completed successfully: {DB_FILE_NAME}")
        return True
    except Exception as e:
        logger.error(f"S3 restore failed: {e}")
        return False