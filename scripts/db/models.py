from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

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
    created_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))
    updated_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')), onupdate=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))

class SPOC(Base):
    __tablename__ = "spocs"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    name = Column(String)
    phone = Column(String)
    email_id = Column(String)
    location = Column(String)
    status = Column(String, default="active")
    created_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))
    updated_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')), onupdate=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))
    
    company = relationship("Company")

class RequirementStatus(Base):
    __tablename__ = "requirement_status"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, unique=True, index=True)

class CandidateStatus(Base):
    __tablename__ = "candidate_status"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, unique=True, index=True)
    stage = Column(String)

class Requirement(Base):
    __tablename__ = "requirements"
    requirement_id = Column(Integer, primary_key=True, index=True)
    created_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))
    company_id = Column(Integer, ForeignKey("companies.id"))
    spoc_id = Column(Integer, ForeignKey("spocs.id"))
    key_skill = Column(String)
    jd = Column(String)
    status_id = Column(Integer, ForeignKey("requirement_status.id"))
    recruiter_name = Column(String)
    closed_date = Column(DateTime)
    budget = Column(Float)
    expected_billing_date = Column(Date)
    location = Column(String)
    remarks = Column(String)
    req_cust_ref_id = Column(String)
    role = Column(String)
    updated_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')), onupdate=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))
    
    company = relationship("Company")
    spoc = relationship("SPOC")
    status = relationship("RequirementStatus")

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    skills = Column(String)
    experience_years = Column(Integer)
    current_location = Column(String)
    preferred_location = Column(String)
    current_ctc = Column(Float)
    expected_ctc = Column(Float)
    notice_period = Column(String)
    status = Column(Integer, default=1)
    created_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))
    updated_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')), onupdate=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True)
    reference = Column(String)
    company_id = Column(Integer, ForeignKey("companies.id"))
    po_number = Column(String)
    amount = Column(Float)
    raised_date = Column(Date)
    due_date = Column(Date)
    status = Column(String, default="pending")
    remarks = Column(String)
    
    company = relationship("Company")

class ProcessProfile(Base):
    __tablename__ = "process_profiles"
    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.requirement_id"))
    recruiter_name = Column(String)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    status = Column(Integer)
    remarks = Column(String)
    
    requirement = relationship("Requirement")
    candidate = relationship("Candidate")