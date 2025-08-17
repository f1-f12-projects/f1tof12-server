from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
from boto3 import client
import os

DB_FILE_NAME = os.getenv('DB_FILE_NAME', 'f1tof12.db')
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{DB_FILE_NAME}")
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
        s3_client.upload_file(DB_FILE, S3_BUCKET, DB_FILE_NAME)
        return True
    except Exception as e:
        print(f"S3 backup failed: {e}")
        return False

def restore_from_s3():
    """Download SQLite database from S3"""
    try:
        s3_client.download_file(S3_BUCKET, DB_FILE_NAME, DB_FILE)
        return True
    except Exception as e:
        print(f"S3 restore failed: {e}")
        return False