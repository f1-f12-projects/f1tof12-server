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
    requirement_id: Optional[int] = None

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
    profile_id: int
    status: int = 1
    remarks: Optional[str] = None

@router.post("/add")
def add_profile(profile: ProfileCreate, user_info: dict = Depends(require_recruiter)):
    try:
        db = get_database()
        # Extract requirement_id before creating profile
        requirement_id = profile.requirement_id
        profile_dict = profile.dict()
        profile_dict.pop('requirement_id', None)  # Remove requirement_id from profile data
        
        profile_data = db.profile.create_profile(profile_dict)

        # If requirement_id is passed, then update process_profile record with profile_id details
        if requirement_id:
            process_profile_data = {
                "requirement_id": requirement_id,
                "recruiter_name": user_info.get('username', 'unknown'),
                "status": 2,
                "profile_id": profile_data['id'],
                "remarks": ""
            }
            db.process_profile.upsert_process_profile(process_profile_data)
        return success_response(profile_data, "Profile added successfully")
    except Exception as e:
        handle_error(e, "add profile")

@router.get("/list")
def list_profiles(user_info: dict = Depends(require_recruiter)):
    try:
        db = get_database()
        profiles_data = db.profile.list_profiles()
        return success_response(profiles_data, "Profiles retrieved successfully")
    except Exception as e:
        handle_error(e, "list profiles")

@router.get("/profile-statuses")
def get_profile_statuses(user_info: dict = Depends(require_recruiter)):
    try:
        db = get_database()
        statuses_data = db.profile.list_profile_statuses()
        return success_response(statuses_data, "Profile statuses retrieved successfully")
    except Exception as e:
        handle_error(e, "get profile statuses")

@router.get("/{profile_id}")
def get_profile(profile_id: int, user_info: dict = Depends(require_recruiter)):
    try:
        db = get_database()
        profile_data = db.profile.get_profile(profile_id)
        if not profile_data:
            raise HTTPException(status_code=404, detail="Profile not found")
        return success_response(profile_data, "Profile retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "get profile")

@router.put("/{profile_id}/update")
def update_profile(profile_id: int, profile_update: ProfileUpdate, user_info: dict = Depends(require_recruiter)):
    try:
        update_data = {k: v for k, v in profile_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        db = get_database()
        success = db.profile.update_profile(profile_id, update_data)
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
        profile_statuses = db.profile.list_profile_statuses()
        valid_statuses = [status['id'] for status in profile_statuses]
        if status_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status passed.")
        
        success = db.profile.update_profile(profile_id, {"status": status_update.status})
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
        requirements_data = db.requirement.list_requirements()
        return success_response(requirements_data, "Requirements retrieved successfully")
    except Exception as e:
        handle_error(e, "view requirements")

@router.post("/add-to-requirement")
def add_profile_to_requirement(process_profile: ProcessProfileCreate, user_info: dict = Depends(require_recruiter)):
    try:
        db = get_database()
        profile_data = {
            "requirement_id": process_profile.requirement_id,
            "profile_id": process_profile.profile_id,
            "recruiter_name": user_info.get('username'),
            "status": process_profile.status,
            "remarks": process_profile.remarks
        }
        result = db.process_profile.create_process_profile(profile_data)
        return success_response(result, "Profile added to requirement successfully")
    except Exception as e:
        handle_error(e, "add profile to requirement")