from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from boto3 import client
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

DB_FILE_NAME = os.getenv('DB_FILE_NAME', 'f1tof12.db')
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(tempfile.gettempdir(), DB_FILE_NAME)}")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

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
DB_FILE = os.getenv('DB_FILE_PATH', os.path.join(tempfile.gettempdir(), DB_FILE_NAME))

def backup_to_s3():
    """Upload SQLite database to S3"""
    try:
        s3_client.upload_file(DB_FILE, S3_BUCKET, DB_FILE_NAME)
        return True
    except Exception as e:
        logger.error(f"S3 backup failed: {e}")
        return False

def restore_from_s3():
    """Download SQLite database from S3"""
    try:
        s3_client.download_file(S3_BUCKET, DB_FILE_NAME, DB_FILE)
        return True
    except Exception as e:
        logger.error(f"S3 restore failed: {e}")
        return False