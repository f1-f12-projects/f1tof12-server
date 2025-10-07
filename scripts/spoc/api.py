from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from scripts.db.database_factory import get_database
from auth import require_manager
from scripts.utils.response import success_response, handle_error
import logging

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
def add_spoc(spoc: SPOCCreate, user_info: dict = Depends(require_manager)):
    try:
        db = get_database()
        spoc_data = db.spoc.create_spoc(
            spoc.company_id,
            spoc.name,
            spoc.phone,
            spoc.email_id,
            spoc.location,
            spoc.status
        )
        return success_response(spoc_data, "SPOC added successfully")
    except Exception as e:
        handle_error(e, "add SPOC")

@router.get("/spoc/list")
def list_spocs(user_info: dict = Depends(require_manager)):
    try:
        db = get_database()
        spocs_data = db.spoc.list_spocs()
        return success_response(spocs_data, "SPOCs retrieved successfully")
    except Exception as e:
        handle_error(e, "list SPOCs")

@router.put("/spoc/{spoc_id}/update")
def update_spoc(spoc_id: int, spoc_update: SPOCUpdate, user_info: dict = Depends(require_manager)):
    try:
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
        
        if not update_data:
            raise HTTPException(status_code=400, detail={
                "error": "NO_UPDATE_FIELDS",
                "message": "No valid fields to update",
                "code": "SPOC_400"
            })
        
        db = get_database()
        success = db.spoc.update_spoc(spoc_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail={
                "error": "SPOC_NOT_FOUND",
                "message": "SPOC not found",
                "code": "SPOC_404"
            })
        
        return success_response(message="SPOC updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "update SPOC")