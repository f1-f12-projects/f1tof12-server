from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from boto3 import client
import os
import logging
from scripts.db.models import Base, User, Company, SPOC, Invoice
from scripts.db.config import DATABASE_URL, TMP_DB_PATH, DB_FILE_NAME, S3_BUCKET

# Configure logging for CloudWatch
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS S3 integration
s3_client = client('s3')

def backup_to_s3():
    """Upload SQLite database to S3"""
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
        logger.info(f"Successfully restored database from S3")
        return True
    except s3_client.exceptions.NoSuchKey:
        logger.info(f"Database file {DB_FILE_NAME} not found in S3 bucket {S3_BUCKET}")
        return False
    except Exception as e:
        logger.error(f"S3 restore failed: {e}")
        return False

def init_database():
    tmp_dir = os.path.dirname(TMP_DB_PATH)
    os.makedirs(tmp_dir, exist_ok=True)
    
    if not os.path.exists(TMP_DB_PATH):
        if not restore_from_s3():
            # Create empty database file
            with open(TMP_DB_PATH, 'w') as f:
                pass
            os.chmod(TMP_DB_PATH, 0o666)

# Initialize database
init_database()

# Simple SQLite connection
sqlite_args = {
    "check_same_thread": False,
    "timeout": 20
}

engine = create_engine(DATABASE_URL, connect_args=sqlite_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create tables: {e}")