from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

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
    po_number = Column(String)
    amount = Column(Float)
    raised_date = Column(Date)
    due_date = Column(Date)
    status = Column(String, default="pending")
    remarks = Column(String)
    
    company = relationship("Company")