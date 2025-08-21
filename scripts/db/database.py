from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from boto3 import client
import os
import shutil
import logging
from scripts.db.models import Base, User, Company, SPOC, Invoice

logger = logging.getLogger(__name__)

DB_FILE_NAME = os.getenv('DB_FILE_NAME', 'f1tof12.db')
TMP_DB_PATH = os.path.join(os.getcwd(), DB_FILE_NAME)
DATABASE_URL = f"sqlite:///{TMP_DB_PATH}"

# Ensure writable database location
os.makedirs(os.path.dirname(TMP_DB_PATH), exist_ok=True)
if not os.path.exists(TMP_DB_PATH):
    if os.path.exists(DB_FILE_NAME):
        shutil.copy2(DB_FILE_NAME, TMP_DB_PATH)
    else:
        open(TMP_DB_PATH, 'w').close()
os.chmod(TMP_DB_PATH, 0o666)
os.chmod(os.path.dirname(TMP_DB_PATH), 0o777)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)

# AWS S3 integration
s3_client = client('s3')
S3_BUCKET = os.getenv('S3_BUCKET', 'f1tof12-db-backup')
DB_FILE = DB_FILE_NAME

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