import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from scripts.db.database_factory import get_database
from auth import require_recruiter
from scripts.utils.response import success_response, handle_error
from scripts.utils.remarks import append_remarks
from typing import Optional, Dict, Any
from datetime import date

logger = logging.getLogger(__name__)

class StatusUpdate(BaseModel):
    status: int
    remarks: Optional[str] = None
    accepted_offer: Optional[float] = None
    joining_date: Optional[date] = None

class RemarksUpdate(BaseModel):
    remarks: str

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
    status: int = 1
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
    status: Optional[int] = None
    remarks: Optional[str] = None
    accepted_offer: Optional[float] = None
    joining_date: Optional[date] = None

class ProcessProfileCreate(BaseModel):
    requirement_id: int
    profile_id: int
    remarks: Optional[str] = None

class DateRangeRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

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
                "profile_id": profile_data['id'],
                "remarks": "",
                "actively_working": "Yes"
            }
            db.process_profile.upsert_process_profile(process_profile_data)
        return success_response(profile_data, "Profile added successfully")
    except Exception as e:
        handle_error(e, "add profile")

@router.post("/by-date-range")
def get_profiles_by_date_range(date_range: DateRangeRequest, user_info: dict = Depends(require_recruiter)):
    # Use provided dates or default to current week
    start_date = date_range.start_date or "2025-11-03"
    end_date = date_range.end_date or "2025-11-09"
    
    logger.info(f"Received start_date: {start_date}, end_date: {end_date}")
    try:
        from datetime import datetime
        
        # Convert string dates to date objects
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        db = get_database()
        user_role = user_info.get('role')
        
        # If user is lead or manager, show all profiles (no recruiter filter)
        # If user is recruiter, show only their profiles
        recruiter_name = None if user_role in ['lead', 'manager'] else user_info.get('username')
        
        profiles_data = db.profile.get_profiles_by_date_range(start_date_obj, end_date_obj, recruiter_name)
        result = success_response(profiles_data, "Profiles retrieved successfully")
        logging.info(f"EXIT: get_profiles_by_date_range - result count={len(profiles_data)}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"ERROR: get_profiles_by_date_range - {e}")
        handle_error(e, "get profiles by date range")

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
        logger.error("HTTPException in get profile")
        raise
    except Exception as e:
        handle_error(e, "get profile")

@router.put("/{profile_id}/update")
def update_profile(profile_id: int, profile_update: ProfileUpdate, user_info: dict = Depends(require_recruiter)):
    try:
        logging.info(f"Updating profile id: {profile_id} with data: {profile_update.dict()}")
        update_data = profile_update.dict(exclude_none=True)
        logging.info(f"Filtered update_data: {update_data}")
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        db = get_database()
        
        # Handle remarks appending if provided
        if 'remarks' in update_data:
            profile_data = db.profile.get_profile(profile_id)
            if not profile_data:
                raise HTTPException(status_code=404, detail="Profile not found")
            
            existing_remarks = profile_data.get('remarks', '') or ''
            update_data['remarks'] = append_remarks(existing_remarks, update_data['remarks'], user_info.get('username', 'unknown'))
        
        success = db.profile.update_profile(profile_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return success_response(message="Profile updated successfully")
    except HTTPException:
        logger.error("HTTPException in update profile")
        raise
    except Exception as e:
        handle_error(e, "update profile")

@router.put("/{profile_id}/status")
def update_status(profile_id: int, status_update: StatusUpdate, user_info: dict = Depends(require_recruiter)):
    try:
        db = get_database()
        
        # Check if profile exists first
        profile_data = db.profile.get_profile(profile_id)
        if not profile_data:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Validate status value
        profile_statuses = db.profile.list_profile_statuses()
        valid_statuses = [status['id'] for status in profile_statuses]
        if status_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status passed.")
        
        # Check if any optional fields are provided
        has_optional_fields = (
            status_update.accepted_offer is not None or 
            status_update.joining_date is not None or 
            status_update.remarks is not None
        )
        
        if not has_optional_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        update_data: Dict[str, Any] = {"status": status_update.status}
        
        # Handle accepted_offer if provided
        if status_update.accepted_offer is not None:
            update_data['accepted_offer'] = status_update.accepted_offer
        
        # Handle joining_date if provided
        if status_update.joining_date is not None:
            update_data['joining_date'] = status_update.joining_date
        
        # Handle remarks if provided
        if status_update.remarks:
            existing_remarks = profile_data.get('remarks', '') or ''
            update_data['remarks'] = append_remarks(existing_remarks, status_update.remarks, user_info.get('username', 'unknown'))
        
        success = db.profile.update_profile(profile_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return success_response(message="Status updated successfully")
    except HTTPException:
        logger.error("HTTPException in profile update status")
        raise
    except Exception as e:
        logger.error(f"Error in update status: {str(e)}")
        handle_error(e, "update status")

@router.put("/{profile_id}/remarks")
def update_remarks(profile_id: int, remarks_update: RemarksUpdate, user_info: dict = Depends(require_recruiter)):
    try:
        db = get_database()
        profile_data = db.profile.get_profile(profile_id)
        if not profile_data:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        existing_remarks = profile_data.get('remarks', '') or ''
        updated_remarks = append_remarks(existing_remarks, remarks_update.remarks, user_info.get('username', 'unknown'))
        
        success = db.profile.update_profile(profile_id, {"remarks": updated_remarks})
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return success_response(message="Remarks updated successfully")
    except HTTPException:
        logger.error("HTTPException in profile update remarks")
        raise
    except Exception as e:
        handle_error(e, "update remarks")

@router.post("/add-to-requirement")
def add_profile_to_requirement(process_profile: ProcessProfileCreate, user_info: dict = Depends(require_recruiter)):
    try:
        db = get_database()
        profile_data = {
            "requirement_id": process_profile.requirement_id,
            "profile_id": process_profile.profile_id,
            "recruiter_name": user_info.get('username'),
            "remarks": process_profile.remarks
        }
        result = db.process_profile.create_process_profile(profile_data)
        return success_response(result, "Profile added to requirement successfully")
    except Exception as e:
        handle_error(e, "add profile to requirement")



