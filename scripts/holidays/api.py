from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import date as Date
from auth import require_hr, get_user_info
from scripts.db.database_factory import get_database
from scripts.utils.response import success_response, handle_error
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class HolidayRequest(BaseModel):
    financial_year_id: int
    name: str
    date: Date
    is_mandatory: Optional[bool] = True

class HolidayUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[Date] = None
    is_mandatory: Optional[bool] = None

class HolidaySelectionRequest(BaseModel):
    holiday_ids: List[int]
    
    @field_validator('holiday_ids')
    @classmethod
    def validate_holiday_ids(cls, v):
        if len(v) != 2:
            raise ValueError('Must select exactly 2 optional holidays')
        return v

@router.post("/holidays")
def create_holiday(request: HolidayRequest, user_info: dict = Depends(require_hr)):
    logger.info(f"[ENTRY] Create holiday API called by: {user_info['username']}")
    
    try:
        db = get_database()
        
        # Validate financial year exists
        financial_year = db.financial_year.get_financial_year_by_id(request.financial_year_id)
        if not financial_year:
            raise HTTPException(status_code=404, detail={
                "error": "FINANCIAL_YEAR_NOT_FOUND",
                "message": "Financial year not found",
                "code": "FY_404"
            })
        
        # Check if mandatory holiday limit reached (8 max)
        if request.is_mandatory:
            mandatory_holidays = db.holiday.get_mandatory_holidays(request.financial_year_id)
            if len(mandatory_holidays) >= 8:
                raise HTTPException(status_code=400, detail={
                    "error": "MANDATORY_LIMIT_REACHED",
                    "message": "Maximum 8 mandatory holidays allowed per year",
                    "code": "HOL_400"
                })
        
        holiday_id = db.holiday.create_holiday(
            financial_year_id=request.financial_year_id,
            name=request.name,
            date=request.date,
            is_mandatory=request.is_mandatory
        )
        
        logger.info("[EXIT] Create holiday API successful")
        return success_response({"id": holiday_id}, "Holiday created successfully")
        
    except HTTPException as e:
        logger.error(f"[ERROR] Create holiday API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "create holiday")

@router.get("/holidays/year/{financial_year_id}")
def get_holidays_by_year(financial_year_id: int, user_info: dict = Depends(get_user_info)):
    logger.info(f"[ENTRY] Get holidays by year API called by: {user_info['username']}")
    
    try:
        db = get_database()
        
        # Validate financial year exists
        financial_year = db.financial_year.get_financial_year_by_id(financial_year_id)
        if not financial_year:
            raise HTTPException(status_code=404, detail={
                "error": "FINANCIAL_YEAR_NOT_FOUND",
                "message": "Financial year not found",
                "code": "FY_404"
            })
        
        holidays = db.holiday.get_holidays_by_year(financial_year_id)
        
        logger.info("[EXIT] Get holidays by year API successful")
        return success_response(holidays, "Holidays retrieved successfully")
        
    except HTTPException as e:
        logger.error(f"[ERROR] Get holidays by year API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "get holidays by year")

@router.get("/holidays/optional/{financial_year_id}")
def get_optional_holidays(financial_year_id: int, user_info: dict = Depends(get_user_info)):
    logger.info(f"[ENTRY] Get optional holidays API called by: {user_info['username']}")
    
    try:
        db = get_database()
        
        # Validate financial year exists
        financial_year = db.financial_year.get_financial_year_by_id(financial_year_id)
        if not financial_year:
            raise HTTPException(status_code=404, detail={
                "error": "FINANCIAL_YEAR_NOT_FOUND",
                "message": "Financial year not found",
                "code": "FY_404"
            })
        
        optional_holidays = db.holiday.get_optional_holidays(financial_year_id)
        
        logger.info("[EXIT] Get optional holidays API successful")
        return success_response(optional_holidays, "Optional holidays retrieved successfully")
        
    except HTTPException as e:
        logger.error(f"[ERROR] Get optional holidays API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "get optional holidays")

@router.post("/holidays/select/{financial_year_id}")
def select_optional_holidays(financial_year_id: int, request: HolidaySelectionRequest, user_info: dict = Depends(get_user_info)):
    logger.info(f"[ENTRY] Select optional holidays API called by: {user_info['username']}")
    
    try:
        db = get_database()
        
        # Validate financial year exists
        financial_year = db.financial_year.get_financial_year_by_id(financial_year_id)
        if not financial_year:
            raise HTTPException(status_code=404, detail={
                "error": "FINANCIAL_YEAR_NOT_FOUND",
                "message": "Financial year not found",
                "code": "FY_404"
            })
        
        # Check if user has already selected holidays for this year
        existing_selections = db.holiday.get_user_selected_holidays(user_info['username'], financial_year_id)
        if existing_selections:
            raise HTTPException(status_code=400, detail={
                "error": "HOLIDAYS_ALREADY_SELECTED",
                "message": "Optional holidays already selected for this financial year",
                "code": "HOL_400"
            })
        
        # Validate all holiday IDs are optional holidays for this year
        optional_holidays = db.holiday.get_optional_holidays(financial_year_id)
        optional_holiday_ids = [h['id'] for h in optional_holidays]
        
        for holiday_id in request.holiday_ids:
            if holiday_id not in optional_holiday_ids:
                raise HTTPException(status_code=400, detail={
                    "error": "INVALID_HOLIDAY_SELECTION",
                    "message": f"Holiday ID {holiday_id} is not an optional holiday for this year",
                    "code": "HOL_400"
                })
        
        success = db.holiday.select_optional_holidays(
            username=user_info['username'],
            holiday_ids=request.holiday_ids,
            financial_year_id=financial_year_id
        )
        
        if not success:
            raise HTTPException(status_code=500, detail={
                "error": "SELECTION_FAILED",
                "message": "Failed to save holiday selection",
                "code": "500"
            })
        
        logger.info("[EXIT] Select optional holidays API successful")
        return success_response({"selected_holidays": request.holiday_ids}, "Optional holidays selected successfully")
        
    except HTTPException as e:
        logger.error(f"[ERROR] Select optional holidays API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "select optional holidays")

@router.get("/holidays/my-holidays/{financial_year_id}")
def get_my_holidays(financial_year_id: int, user_info: dict = Depends(get_user_info)):
    logger.info(f"[ENTRY] Get my holidays API called by: {user_info['username']}")
    
    try:
        db = get_database()
        
        # Validate financial year exists
        financial_year = db.financial_year.get_financial_year_by_id(financial_year_id)
        if not financial_year:
            raise HTTPException(status_code=404, detail={
                "error": "FINANCIAL_YEAR_NOT_FOUND",
                "message": "Financial year not found",
                "code": "FY_404"
            })
        
        user_holidays = db.holiday.get_user_holidays_for_year(user_info['username'], financial_year_id)
        
        logger.info("[EXIT] Get my holidays API successful")
        return success_response(user_holidays, "User holidays retrieved successfully")
        
    except HTTPException as e:
        logger.error(f"[ERROR] Get my holidays API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "get my holidays")

@router.put("/holidays/{holiday_id}")
def update_holiday(holiday_id: int, request: HolidayUpdate, user_info: dict = Depends(require_hr)):
    logger.info(f"[ENTRY] Update holiday API called by: {user_info['username']} for holiday: {holiday_id}")
    
    try:
        db = get_database()
        
        # Check if holiday exists
        existing_holiday = db.holiday.get_holiday_by_id(holiday_id)
        if not existing_holiday:
            raise HTTPException(status_code=404, detail={
                "error": "HOLIDAY_NOT_FOUND",
                "message": "Holiday not found",
                "code": "HOL_404"
            })
        
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.date is not None:
            update_data["date"] = request.date
        if request.is_mandatory is not None:
            # Check mandatory holiday limit if changing to mandatory
            if request.is_mandatory and not existing_holiday['is_mandatory']:
                mandatory_holidays = db.holiday.get_mandatory_holidays(existing_holiday['financial_year_id'])
                if len(mandatory_holidays) >= 8:
                    raise HTTPException(status_code=400, detail={
                        "error": "MANDATORY_LIMIT_REACHED",
                        "message": "Maximum 8 mandatory holidays allowed per year",
                        "code": "HOL_400"
                    })
            update_data["is_mandatory"] = request.is_mandatory
        
        if not update_data:
            raise HTTPException(status_code=400, detail={
                "error": "NO_UPDATE_DATA",
                "message": "No data provided for update",
                "code": "HOL_400"
            })
        
        success = db.holiday.update_holiday(holiday_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail={
                "error": "UPDATE_FAILED",
                "message": "Failed to update holiday",
                "code": "500"
            })
        
        logger.info("[EXIT] Update holiday API successful")
        return success_response({"id": holiday_id}, "Holiday updated successfully")
        
    except HTTPException as e:
        logger.error(f"[ERROR] Update holiday API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "update holiday")

@router.delete("/holidays/{holiday_id}")
def delete_holiday(holiday_id: int, user_info: dict = Depends(require_hr)):
    logger.info(f"[ENTRY] Delete holiday API called by: {user_info['username']} for holiday: {holiday_id}")
    
    try:
        db = get_database()
        
        # Check if holiday exists
        existing_holiday = db.holiday.get_holiday_by_id(holiday_id)
        if not existing_holiday:
            raise HTTPException(status_code=404, detail={
                "error": "HOLIDAY_NOT_FOUND",
                "message": "Holiday not found",
                "code": "HOL_404"
            })
        
        success = db.holiday.delete_holiday(holiday_id)
        
        if not success:
            raise HTTPException(status_code=500, detail={
                "error": "DELETE_FAILED",
                "message": "Failed to delete holiday",
                "code": "500"
            })
        
        logger.info("[EXIT] Delete holiday API successful")
        return success_response({"id": holiday_id}, "Holiday deleted successfully")
        
    except HTTPException as e:
        logger.error(f"[ERROR] Delete holiday API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "delete holiday")