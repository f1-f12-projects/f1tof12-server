from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from boto3 import client
import os
import logging
from scripts.db.models import Base, User, Company, SPOC, Invoice
from scripts.db.config import DATABASE_URL, TMP_DB_PATH, DB_FILE_NAME, S3_BUCKET

logger = logging.getLogger(__name__)

# AWS S3 integration
s3_client = client('s3')

def backup_to_s3():
    """Upload SQLite database to S3"""
    logger.info(f"Starting S3 backup to bucket: {S3_BUCKET}")
    try:
        if not os.path.exists(TMP_DB_PATH):
            logger.error(f"Database file not found: {TMP_DB_PATH}")
            return False
        s3_client.upload_file(TMP_DB_PATH, S3_BUCKET, DB_FILE_NAME)
        logger.info(f"S3 backup completed successfully: {DB_FILE_NAME}")
        return True
    except Exception as e:
        logger.error(f"S3 backup failed: {e}")
        return False

def restore_from_s3():
    """Download SQLite database from S3"""
    try:
        s3_client.download_file(S3_BUCKET, DB_FILE_NAME, TMP_DB_PATH)
        return True
    except Exception as e:
        logger.error(f"S3 restore failed: {e}")
        return False

# Initialize database
if not os.path.exists(TMP_DB_PATH):
    restore_from_s3()

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)