from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from scripts.db.database import SPOC, Company, User
from scripts.db.session import get_db_with_backup
from auth import verify_cognito_token
from scripts.utils.response import success_response, handle_error
import logging
import json

logger = logging.getLogger(__name__)

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
def add_spoc(spoc: SPOCCreate, db: Session = Depends(get_db_with_backup), current_user: User = Depends(verify_cognito_token)):
    try:
        company = db.query(Company).filter(Company.id == spoc.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail={
                "error": "COMPANY_NOT_FOUND",
                "message": "Company not found",
                "code": "COMP_404"
            })
        
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
        return success_response(message="SPOC added successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "add SPOC")

@router.get("/spoc/list")
def list_spocs(db: Session = Depends(get_db_with_backup), current_user: User = Depends(verify_cognito_token)):
    try:
        spocs = db.query(SPOC).all()
        spocs_data = [{"id": spoc.id, "company_id": spoc.company_id, "name": spoc.name, "phone": spoc.phone, "email_id": spoc.email_id, "location": spoc.location, "status": spoc.status, "created_date": spoc.created_date, "updated_date": spoc.updated_date} for spoc in spocs]
        return success_response(spocs_data, "SPOCs retrieved successfully")
    except Exception as e:
        handle_error(e, "list SPOCs")

@router.put("/spoc/{spoc_id}/update")
def update_spoc(spoc_id: int, spoc_update: SPOCUpdate, db: Session = Depends(get_db_with_backup), current_user: User = Depends(verify_cognito_token)):
    logger.info(f"Entering update_spoc for SPOC ID: {spoc_id}")
    logger.info(f"Raw input data: {json.dumps(spoc_update.dict(), default=str)}")
    try:
        # Check if SPOC exists first
        existing_spoc = db.query(SPOC).filter(SPOC.id == spoc_id).first()
        if not existing_spoc:
            logger.warning(f"SPOC {spoc_id} not found in database")
            raise HTTPException(status_code=404, detail={
                "error": "SPOC_NOT_FOUND",
                "message": "SPOC not found",
                "code": "SPOC_404"
            })
        
        logger.info(f"Found existing SPOC: {existing_spoc.name}")
        
        update_data = {}
        if spoc_update.name:
            update_data['name'] = spoc_update.name
        if spoc_update.phone:
            update_data['phone'] = spoc_update.phone
        if spoc_update.email_id:
            update_data['email_id'] = spoc_update.email_id
        if spoc_update.location:
            update_data['location'] = spoc_update.location
        if spoc_update.status:
            update_data['status'] = spoc_update.status

        logger.info(f"Final update data for SPOC {spoc_id}: {json.dumps(update_data, default=str)}")
        
        if not update_data:
            logger.warning(f"No valid fields to update for SPOC {spoc_id}")
            raise HTTPException(status_code=400, detail={
                "error": "NO_UPDATE_FIELDS",
                "message": "No valid fields to update",
                "code": "SPOC_400"
            })
        
        result = db.query(SPOC).filter(SPOC.id == spoc_id).update(update_data)
        logger.info(f"Database update result: {result} rows affected")
        
        db.commit()
        logger.info(f"Successfully updated SPOC {spoc_id}")
        return success_response(message="SPOC updated successfully")
    except HTTPException:
        logger.warning(f"HTTP exception occurred while updating SPOC {spoc_id}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating SPOC {spoc_id}: {str(e)}")
        handle_error(e, "update SPOC")