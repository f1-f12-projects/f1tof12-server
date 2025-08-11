from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, field_validator
from scripts.db.database import get_db, Company

router = APIRouter()

class CompanyCreate(BaseModel):
    name: str
    spoc: str
    email_id: str
    status: str = "active"

class CompanyStatusUpdate(BaseModel):
    status: str
    
    @field_validator('status')
    def validate_status(cls, v):
        if v not in ['active', 'inactive']:
            raise ValueError('Status must be either "active" or "inactive"')
        return v

@router.post("/register", response_model=dict)
def register(company: CompanyCreate, db: Session = Depends(get_db)):
    db_company = db.query(Company).filter(func.lower(Company.name) == func.lower(company.name)).first()
    if db_company:
        raise HTTPException(status_code=409, detail="Company already registered")
    
    db_company = Company(name=company.name, spoc=company.spoc, email_id=company.email_id, status=company.status)
    db.add(db_company)
    db.commit()
    return {"message": "Company registered successfully"}

@router.get("/companies")
def list_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).all()
    return [{"id": company.id, "name": company.name, "spoc": company.spoc, "email_id": company.email_id, "status": company.status} for company in companies]

@router.put("/companies/{company_id}/status")
def update_company_status(company_id: int, status_update: CompanyStatusUpdate, db: Session = Depends(get_db)):
    result = db.query(Company).filter(Company.id == company_id).update({"status": status_update.status})
    if result == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db.commit()
    return {"message": "Company status updated successfully"}