from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
from boto3 import client
import os
import shutil

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
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    spoc = Column(String)
    email_id = Column(String)
    status = Column(String, default="active")
    created_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class SPOC(Base):
    __tablename__ = "spocs"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    name = Column(String)
    phone = Column(String)
    email_id = Column(String)
    location = Column(String)
    status = Column(String, default="active")
    created_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    company = relationship("Company")

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True)
    reference = Column(String)
    company_id = Column(Integer, ForeignKey("companies.id"))
    raised_date = Column(Date)
    due_date = Column(Date)
    status = Column(String, default="pending")
    remarks = Column(String)
    
    company = relationship("Company")

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
    try:
        s3_client.upload_file(TMP_DB_PATH, S3_BUCKET, DB_FILE_NAME)
        return True
    except Exception as e:
        print(f"S3 backup failed: {e}")
        return False

def restore_from_s3():
    """Download SQLite database from S3"""
    try:
        s3_client.download_file(S3_BUCKET, DB_FILE_NAME, TMP_DB_PATH)
        return True
    except Exception as e:
        print(f"S3 restore failed: {e}")
        return False