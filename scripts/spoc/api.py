from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from scripts.db.database import get_db, SPOC, Company, User
from auth import verify_cognito_token

router = APIRouter()

class SPOCCreate(BaseModel):
    company_id: int
    name: str
    phone: str
    email_id: str
    location: str
    status: str = "active"

class SPOCUpdate(BaseModel):
    name: str = ''
    phone: str = ''
    email_id: str = ''
    location: str = ''
    status: str = ''
    
    @field_validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ['active', 'inactive']:
            raise ValueError('Status must be either "active" or "inactive"')
        return v

@router.post("/spoc/add")
def add_spoc(spoc: SPOCCreate, db: Session = Depends(get_db), current_user: User = Depends(verify_cognito_token)):
    company = db.query(Company).filter(Company.id == spoc.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db_spoc = SPOC(
        company_id=spoc.company_id,
        name=spoc.name,
        phone=spoc.phone,
        email_id=spoc.email_id,
        location=spoc.location,
        status=spoc.status
    )
    db.add(db_spoc)
    db.commit()
    return {"message": "SPOC added successfully"}

@router.get("/spoc/list")
def list_spocs(db: Session = Depends(get_db), current_user: User = Depends(verify_cognito_token)):
    spocs = db.query(SPOC).all()
    return [{"id": spoc.id, "company_id": spoc.company_id, "name": spoc.name, "phone": spoc.phone, "email_id": spoc.email_id, "location": spoc.location, "status": spoc.status, "created_date": spoc.created_date, "updated_date": spoc.updated_date} for spoc in spocs]

@router.put("/spoc/{spoc_id}/update")
def update_spoc(spoc_id: int, spoc_update: SPOCUpdate, db: Session = Depends(get_db), current_user: User = Depends(verify_cognito_token)):
    update_data = {}
    if spoc_update.name is not None:
        update_data[SPOC.name] = spoc_update.name
    if spoc_update.phone is not None:
        update_data[SPOC.phone] = spoc_update.phone
    if spoc_update.email_id is not None:
        update_data[SPOC.email_id] = spoc_update.email_id
    if spoc_update.location is not None:
        update_data[SPOC.location] = spoc_update.location
    if spoc_update.status is not None:
        update_data[SPOC.status] = spoc_update.status
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    result = db.query(SPOC).filter(SPOC.id == spoc_id).update(update_data)
    if result == 0:
        raise HTTPException(status_code=404, detail="SPOC not found")
    
    db.commit()
    return {"message": "SPOC updated successfully"}