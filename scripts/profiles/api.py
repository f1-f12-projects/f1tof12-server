from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from scripts.db.database_factory import get_database
from auth import require_recruiter, require_lead_or_recruiter
from scripts.utils.response import success_response, handle_error
from typing import Optional

class StatusUpdate(BaseModel):
    status: int

router = APIRouter(prefix="/profiles", tags=["profiles"])

class ProfileCreate(BaseModel):
    name: str
    email: str
    phone: str
    skills: str
    experience_years: int
    current_location: str
    preferred_location: str
    current_ctc: Optional[float] = None
    expected_ctc: Optional[float] = None
    notice_period: Optional[str] = None
    status: str = "New"

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[str] = None
    experience_years: Optional[int] = None
    current_location: Optional[str] = None
    preferred_location: Optional[str] = None
    current_ctc: Optional[float] = None
    expected_ctc: Optional[float] = None
    notice_period: Optional[str] = None
    status: Optional[str] = None

class ProcessProfileCreate(BaseModel):
    requirement_id: int
    candidate_id: int
    status: int = 1
    remarks: Optional[str] = None

@router.post("/add")
def add_profile(profile: ProfileCreate, user_info: dict = Depends(require_recruiter)):
    try:
        db = get_database()
        profile_data = db.create_candidate(profile.dict())
        return success_response(profile_data, "Profile added successfully")
    except Exception as e:
        handle_error(e, "add profile")

@router.get("/list")
def list_profiles(user_info: dict = Depends(require_recruiter)):
    try:
        db = get_database()
        profiles_data = db.list_candidates()
        return success_response(profiles_data, "Profiles retrieved successfully")
    except Exception as e:
        handle_error(e, "list profiles")

@router.put("/{profile_id}/update")
def update_profile(profile_id: int, profile_update: ProfileUpdate, user_info: dict = Depends(require_recruiter)):
    try:
        update_data = {k: v for k, v in profile_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        db = get_database()
        success = db.update_candidate(profile_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return success_response(message="Profile updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "update profile")

@router.put("/{profile_id}/status")
def update_status(profile_id: int, status_update: StatusUpdate, user_info: dict = Depends(require_recruiter)):
    try:
        # Validate status value
        db = get_database()
        candidate_statuses = db.list_candidate_statuses()
        valid_statuses = [status['id'] for status in candidate_statuses]
        if status_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status passed.")
        
        success = db.update_candidate(profile_id, {"status": status_update.status})
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return success_response(message="Status updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "update status")

@router.get("/view-requirements")
def view_requirements(user_info: dict = Depends(require_recruiter)):
    try:
        db = get_database()
        requirements_data = db.list_requirements()
        return success_response(requirements_data, "Requirements retrieved successfully")
    except Exception as e:
        handle_error(e, "view requirements")

@router.post("/add-to-requirement")
def add_profile_to_requirement(process_profile: ProcessProfileCreate, user_info: dict = Depends(require_recruiter)):
    try:
        db = get_database()
        profile_data = {
            "requirement_id": process_profile.requirement_id,
            "candidate_id": process_profile.candidate_id,
            "recruiter_name": user_info.get('username'),
            "status": process_profile.status,
            "remarks": process_profile.remarks
        }
        result = db.create_process_profile(profile_data)
        return success_response(result, "Profile added to requirement successfully")
    except Exception as e:
        handle_error(e, "add profile to requirement")