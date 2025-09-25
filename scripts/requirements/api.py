from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from scripts.db.database_factory import get_database
from auth import require_lead, require_lead_or_recruiter
from scripts.utils.response import success_response, handle_error
from .validation import validate_requirement_fields
from typing import Optional, Dict, Any
from datetime import date, datetime
from zoneinfo import ZoneInfo
import boto3
from scripts.constants import AWS_REGION

router = APIRouter(prefix="/requirements", tags=["requirements"])

class RequirementCreate(BaseModel):
    key_skill: str = Field(alias="key_skill")
    jd: str = Field(alias="jd")
    company_id: int = Field(alias="company_id")
    spoc_id: Optional[int] = Field(None, alias="spoc_id")
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
    remarks: Optional[str] = None
    location: Optional[str] = None
    budget: Optional[float] = None
    expected_billing_date: Optional[date] = None
    req_cust_ref_id: Optional[str] = None

class RequirementSPOC(BaseModel):
    spoc_id: int

class RequirementRecruiter(BaseModel):
    recruiter_name: str

class RequirementStatusUpdate(BaseModel):
    status_id: int
    remarks: Optional[str] = None

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

@router.put("/{requirement_id}/spoc")
def set_requirement_spoc(requirement_id: int, spoc_data: RequirementSPOC, user_info: dict = Depends(require_lead)):
    try:
        db = get_database()
        success = db.update_requirement(requirement_id, {"spoc_id": spoc_data.spoc_id})
        if not success:
            raise HTTPException(status_code=404, detail="Requirement not found")
        
        return success_response(message="SPOC assigned to requirement successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "set requirement SPOC")

@router.put("/{requirement_id}/recruiter")
def assign_recruiter(requirement_id: int, recruiter_data: RequirementRecruiter, user_info: dict = Depends(require_lead)):
    try:
        from scripts.users.api import get_cognito_config
        USER_POOL_ID, _, _ = get_cognito_config()
        cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)
        
        try:
            cognito_client.admin_get_user(
                UserPoolId=USER_POOL_ID,
                Username=recruiter_data.recruiter_name
            )
        except:
            raise HTTPException(status_code=400, detail={
                "error": "RECRUITER_NOT_FOUND",
                "message": "Recruiter not found in the system",
                "code": "RCTR_404"
            })
        
        db = get_database()
        success = db.update_requirement(requirement_id, {"recruiter_name": recruiter_data.recruiter_name})
        if not success:
            raise HTTPException(status_code=404, detail="Requirement not found")
        
        return success_response(message="Recruiter assigned to requirement successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "assign recruiter")

@router.put("/{requirement_id}/status")
def update_status_with_remarks(requirement_id: int, status_update: RequirementStatusUpdate, user_info: dict = Depends(require_lead)):
    try:
        db = get_database()
        current_req = db.get_requirement(requirement_id)
        if not current_req:
            raise HTTPException(status_code=404, detail={"error": "REQUIREMENT_NOT_FOUND", "message": "Requirement not found", "code": "REQ_404"})
        
        update_data: Dict[str, Any] = {"status_id": status_update.status_id}
        
        if status_update.status_id in [9, 10]:
            update_data["closed_date"] = datetime.now(ZoneInfo('Asia/Kolkata'))
        
        if status_update.remarks:
            old_remarks = current_req.get('remarks', '')
            current_date = datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%d-%b-%y')
            username = user_info.get('username', 'unknown')
            formatted_remark = f"{current_date} [{username}]: {status_update.remarks}"
            new_remarks = f"{old_remarks}\n{formatted_remark}" if old_remarks else formatted_remark
            update_data["remarks"] = new_remarks
        
        success = db.update_requirement(requirement_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail={"error": "REQUIREMENT_NOT_FOUND", "message": "Requirement not found", "code": "REQ_404"})
        
        return success_response(message="Status and remarks updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "update status with remarks")