from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from scripts.db.database_factory import get_database
from auth import require_lead, require_lead_or_recruiter
from scripts.utils.response import success_response, handle_error
from .validation import validate_requirement_fields
from typing import Optional
from datetime import date, datetime
from zoneinfo import ZoneInfo

router = APIRouter(prefix="/requirements", tags=["requirements"])

class RequirementCreate(BaseModel):
    key_skill: str = Field(alias="key_skill")
    jd: str = Field(alias="jd")
    company_id: int = Field(alias="company_id")
    experience_level: str = Field(alias="experience_level")
    location: str = Field(alias="location")
    budget: Optional[float] = Field(None, alias="budget")
    expected_billing_date: Optional[date] = Field(None, alias="expected_billing_date")
    status_id: int = Field(1, alias="status")
    req_cust_ref_id: Optional[str] = Field(None, alias="req_cust_ref_id")
    created_date: Optional[datetime] = Field(None, alias="created_date")
    
    class Config:
        allow_population_by_field_name = True

class RequirementUpdate(BaseModel):
    key_skill: Optional[str] = None
    jd: Optional[str] = None
    experience_level: Optional[str] = None
    location: Optional[str] = None
    budget: Optional[float] = None
    expected_billing_date: Optional[date] = None
    status: Optional[str] = None
    req_cust_ref_id: Optional[str] = None

@router.post("/add")
def add_requirement(requirement: RequirementCreate, user_info: dict = Depends(require_lead)):
    try:
        validate_requirement_fields(requirement)
        requirement_dict = requirement.dict()
        # Set created_date to current IST time if not provided
        if not requirement_dict.get('created_date'):
            requirement_dict['created_date'] = datetime.now(ZoneInfo('Asia/Kolkata'))
        
        # Map experience_level to remarks for database
        requirement_dict['remarks'] = requirement_dict.pop('experience_level')
        
        # Map status to status_id for database
        if 'status' in requirement_dict:
            requirement_dict['status_id'] = requirement_dict.pop('status')
        
        db = get_database()
        requirement_data = db.create_requirement(requirement_dict)
        return success_response(requirement_data, "Requirement added successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "add requirement")

@router.get("/list")
def list_requirements(user_info: dict = Depends(require_lead_or_recruiter)):
    try:
        db = get_database()
        requirements_data = db.list_requirements()
        return success_response(requirements_data, "Requirements retrieved successfully")
    except Exception as e:
        handle_error(e, "list requirements")

@router.put("/{requirement_id}/update")
def update_requirement(requirement_id: int, requirement_update: RequirementUpdate, user_info: dict = Depends(require_lead)):
    try:
        update_data = {k: v for k, v in requirement_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        db = get_database()
        success = db.update_requirement(requirement_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Requirement not found")
        
        return success_response(message="Requirement updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "update requirement")