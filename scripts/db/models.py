from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
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

class ProfileStatus(Base):
    __tablename__ = "profile_status"
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

class Profile(Base):
    __tablename__ = "profiles"
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
    remarks = Column(String)
    accepted_offer = Column(Float)
    joining_date = Column(Date)
    current_employer = Column(String)
    highest_education = Column(String)
    offer_in_hand = Column(Boolean, default=False)
    variable_pay = Column(Float)
    document_url = Column(String)
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
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    remarks = Column(String)
    actively_working = Column(String, default="Yes")
    
    requirement = relationship("Requirement")
    profile = relationship("Profile")

class Leave(Base):
    __tablename__ = "leaves"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    leave_type = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    days = Column(Integer)
    reason = Column(String)
    status = Column(String, default="pending")
    approver_username = Column(String)
    approver_comments = Column(String)
    created_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))
    updated_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')), onupdate=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))

class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    annual_leave = Column(Integer, default=20)
    sick_leave = Column(Integer, default=10)
    casual_leave = Column(Integer, default=5)
    year = Column(Integer, default=lambda: datetime.now().year)
    created_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))
    updated_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')), onupdate=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))

class FinancialYear(Base):
    __tablename__ = "financial_years"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, unique=True, index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    is_active = Column(Boolean, default=False)
    created_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))
    updated_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')), onupdate=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))

class HolidayCalendar(Base):
    __tablename__ = "holiday_calendar"
    id = Column(Integer, primary_key=True, index=True)
    financial_year_id = Column(Integer, ForeignKey("financial_years.id"))
    name = Column(String)
    date = Column(Date)
    is_mandatory = Column(Boolean, default=True)
    created_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))
    updated_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')), onupdate=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))
    
    financial_year = relationship("FinancialYear")

class UserHolidaySelection(Base):
    __tablename__ = "user_holiday_selections"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    holiday_id = Column(Integer, ForeignKey("holiday_calendar.id"))
    financial_year_id = Column(Integer, ForeignKey("financial_years.id"))
    created_date = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Kolkata')))
    
    holiday = relationship("HolidayCalendar")
    financial_year = relationship("FinancialYear")

