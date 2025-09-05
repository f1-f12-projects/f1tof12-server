from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from scripts.db.database_factory import get_database
from auth import require_lead, require_lead_or_recruiter
from scripts.utils.response import success_response, handle_error
from typing import Optional
from datetime import date

router = APIRouter(prefix="/requirements", tags=["requirements"])

class RequirementCreate(BaseModel):
    title: str
    description: str
    company_id: int
    skills_required: str
    experience_level: str
    location: str
    budget: Optional[float] = None
    deadline: Optional[date] = None
    status: str = "open"

class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    skills_required: Optional[str] = None
    experience_level: Optional[str] = None
    location: Optional[str] = None
    budget: Optional[float] = None
    deadline: Optional[date] = None
    status: Optional[str] = None

@router.post("/add")
def add_requirement(requirement: RequirementCreate, user_info: dict = Depends(require_lead)):
    try:
        db = get_database()
        requirement_data = db.create_requirement(requirement.dict())
        return success_response(requirement_data, "Requirement added successfully")
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