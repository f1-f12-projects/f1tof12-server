from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from scripts.db.database_factory import get_database
from auth import require_manager, require_finance_or_manager
from scripts.utils.response import success_response, handle_error
from scripts.constants import USER_STATUS_ACTIVE, USER_STATUS_INACTIVE
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class CompanyCreate(BaseModel):
    name: str
    spoc: str
    email_id: str
    status: str = USER_STATUS_ACTIVE

class CompanyUpdate(BaseModel):
    spoc: str = ''
    email_id: str = ''
    status: str = ''
    
    @field_validator('status')
    def validate_status(cls, v):
        if v is not None and v not in [USER_STATUS_ACTIVE, USER_STATUS_INACTIVE]:
            raise ValueError(f'Status must be either "{USER_STATUS_ACTIVE}" or "{USER_STATUS_INACTIVE}"')
        return v

@router.post("/customer/register", response_model=dict)
def register(company: CompanyCreate, user_info: dict = Depends(require_manager)):
    logger.info("Entering register method")
    try:
        db = get_database()
        existing_company = db.company.get_company_by_name(company.name)
        if existing_company:
            raise HTTPException(status_code=409, detail={
                "error": "COMPANY_EXISTS",
                "message": "Company already registered",
                "code": "COMP_409"
            })
        
        db.company.create_company(company.name, company.spoc, company.email_id, company.status)
        logger.info("Exiting register method - success")
        return success_response(message="Company registered successfully")
    except HTTPException:
        logger.warning("Exiting register method - HTTP exception")
        raise
    except Exception as e:
        logger.error("Exiting register method - error")
        handle_error(e, "register company")

@router.get("/customer/list")
def list_companies(user_info: dict = Depends(require_finance_or_manager)):
    logger.info("Entering list_companies method")
    try:
        db = get_database()
        companies_data = db.company.list_companies()
        logger.info("Exiting list_companies method - success")
        return success_response(companies_data, "Companies retrieved successfully")
    except Exception as e:
        logger.error("Exiting list_companies method - error")
        handle_error(e, "list companies")

@router.put("/customer/{company_id}/update")
def update_company(company_id: int, company_update: CompanyUpdate, user_info: dict = Depends(require_manager)):
    logger.info(f"Entering update_company method for company_id: {company_id}")
    try:
        update_data = {}
        if company_update.spoc:
            update_data['spoc'] = company_update.spoc
        if company_update.email_id:
            update_data['email_id'] = company_update.email_id
        if company_update.status:
            update_data['status'] = company_update.status
        
        if not update_data:
            raise HTTPException(status_code=400, detail={
                "error": "NO_UPDATE_FIELDS",
                "message": "No valid fields to update",
                "code": "COMP_400"
            })
        
        db = get_database()
        success = db.company.update_company(company_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail={
                "error": "COMPANY_NOT_FOUND",
                "message": "Company not found",
                "code": "COMP_404"
            })
        
        logger.info(f"Company updated successfully")
        return success_response(message="Company updated successfully")
    except HTTPException:
        logger.warning(f"Exiting update_company method - HTTP exception")
        raise
    except Exception as e:
        logger.error(f"Exiting update_company method - error")
        handle_error(e, "update company")