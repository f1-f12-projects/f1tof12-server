from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, field_validator
from scripts.db.database import get_db, Company, SPOC

router = APIRouter()

class CompanyCreate(BaseModel):
    name: str
    spoc: str
    email_id: str
    status: str = "active"

class CompanyUpdate(BaseModel):
    spoc: str = ''
    email_id: str = ''
    status: str = ''
    
    @field_validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ['active', 'inactive']:
            raise ValueError('Status must be either "active" or "inactive"')
        return v

@router.post("/customer/register", response_model=dict)
def register(company: CompanyCreate, db: Session = Depends(get_db)):
    db_company = db.query(Company).filter(func.lower(Company.name) == func.lower(company.name)).first()
    if db_company:
        raise HTTPException(status_code=409, detail="Company already registered")
    
    db_company = Company(name=company.name, spoc=company.spoc, email_id=company.email_id, status=company.status)
    db.add(db_company)
    db.commit()
    return {"message": "Company registered successfully"}

@router.get("/customer/list")
def list_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).all()
    return [{"id": company.id, "name": company.name, "spoc": company.spoc, "email_id": company.email_id, "status": company.status, "created_date": company.created_date, "updated_date": company.updated_date} for company in companies]

@router.put("/customer/{company_id}/update")
def update_company(company_id: int, company_update: CompanyUpdate, db: Session = Depends(get_db)):
    update_data = {}
    if company_update.spoc is not None:
        update_data[Company.spoc] = company_update.spoc
    if company_update.email_id is not None:
        update_data[Company.email_id] = company_update.email_id
    if company_update.status is not None:
        update_data[Company.status] = company_update.status
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    result = db.query(Company).filter(Company.id == company_id).update(update_data)
    if result == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db.commit()
    return {"message": "Company updated successfully"}