from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from auth import require_hr, get_user_info
from scripts.db.database_factory import get_database
from scripts.utils.response import success_response, handle_error
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class FinancialYearRequest(BaseModel):
    year: int
    start_date: date
    end_date: date
    is_active: Optional[bool] = False

class FinancialYearUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

@router.post("/financial-years")
def create_financial_year(request: FinancialYearRequest, user_info: dict = Depends(require_hr)):
    logger.info(f"[ENTRY] Create financial year API called by: {user_info['username']}")
    
    try:
        db = get_database()
        
        # Check if year already exists
        existing_years = db.financial_year.get_all_financial_years()
        if any(fy['year'] == request.year for fy in existing_years):
            raise HTTPException(status_code=409, detail={
                "error": "YEAR_EXISTS",
                "message": f"Financial year {request.year} already exists",
                "code": "FY_409"
            })
        
        year_id = db.financial_year.create_financial_year(
            year=request.year,
            start_date=request.start_date,
            end_date=request.end_date,
            is_active=request.is_active
        )
        
        logger.info("[EXIT] Create financial year API successful")
        return success_response({"id": year_id}, "Financial year created successfully")
        
    except HTTPException as e:
        logger.error(f"[ERROR] Create financial year API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "create financial year")

@router.get("/financial-years")
def get_all_financial_years(user_info: dict = Depends(get_user_info)):
    logger.info(f"[ENTRY] Get all financial years API called by: {user_info['username']}")
    
    try:
        db = get_database()
        years = db.financial_year.get_all_financial_years()
        
        logger.info("[EXIT] Get all financial years API successful")
        return success_response(years, "Financial years retrieved successfully")
        
    except Exception as e:
        handle_error(e, "get all financial years")

@router.get("/financial-years/active")
def get_active_financial_year(user_info: dict = Depends(require_hr)):
    logger.info(f"[ENTRY] Get active financial year API called by: {user_info['username']}")
    
    try:
        db = get_database()
        active_year = db.financial_year.get_active_financial_year()
        
        if not active_year:
            raise HTTPException(status_code=404, detail={
                "error": "NO_ACTIVE_YEAR",
                "message": "No active financial year found",
                "code": "FY_404"
            })
        
        logger.info("[EXIT] Get active financial year API successful")
        return success_response(active_year, "Active financial year retrieved successfully")
        
    except HTTPException as e:
        logger.error("[ERROR] Get active financial year API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "get active financial year")

@router.put("/financial-years/{year_id}")
def update_financial_year(year_id: int, request: FinancialYearUpdate, user_info: dict = Depends(require_hr)):
    logger.info(f"[ENTRY] Update financial year API called by: {user_info['username']} for year: {year_id}")
    
    try:
        db = get_database()
        
        # Check if year exists
        existing_year = db.financial_year.get_financial_year_by_id(year_id)
        if not existing_year:
            raise HTTPException(status_code=404, detail={
                "error": "YEAR_NOT_FOUND",
                "message": "Financial year not found",
                "code": "FY_404"
            })
        
        update_data = {}
        if request.start_date is not None:
            update_data["start_date"] = request.start_date
        if request.end_date is not None:
            update_data["end_date"] = request.end_date
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        
        if not update_data:
            raise HTTPException(status_code=400, detail={
                "error": "NO_UPDATE_DATA",
                "message": "No data provided for update",
                "code": "FY_400"
            })
        
        success = db.financial_year.update_financial_year(year_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail={
                "error": "UPDATE_FAILED",
                "message": "Failed to update financial year",
                "code": "500"
            })
        
        logger.info("[EXIT] Update financial year API successful")
        return success_response({"id": year_id}, "Financial year updated successfully")
        
    except HTTPException as e:
        logger.error(f"[ERROR] Update financial year API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "update financial year")

@router.post("/financial-years/{year_id}/activate")
def activate_financial_year(year_id: int, user_info: dict = Depends(require_hr)):
    logger.info(f"[ENTRY] Activate financial year API called by: {user_info['username']} for year: {year_id}")
    
    try:
        db = get_database()
        
        # Check if year exists
        existing_year = db.financial_year.get_financial_year_by_id(year_id)
        if not existing_year:
            raise HTTPException(status_code=404, detail={
                "error": "YEAR_NOT_FOUND",
                "message": "Financial year not found",
                "code": "FY_404"
            })
        
        success = db.financial_year.set_active_financial_year(year_id)
        
        if not success:
            raise HTTPException(status_code=500, detail={
                "error": "ACTIVATION_FAILED",
                "message": "Failed to activate financial year",
                "code": "500"
            })
        
        logger.info("[EXIT] Activate financial year API successful")
        return success_response({"id": year_id}, "Financial year activated successfully")
        
    except HTTPException as e:
        logger.error(f"[ERROR] Activate financial year API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "activate financial year")

