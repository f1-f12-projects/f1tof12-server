from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime, timedelta
from auth import get_user_info, require_leave_management, require_hr, validate_cognito_user
from scripts.db.database_factory import get_database
from scripts.utils.response import success_response, handle_error
from scripts.constants import LEAVE_TYPES
import logging


logger = logging.getLogger(__name__)
router = APIRouter()

def calculate_leave_days(start_date: date, end_date: date, leave_type: str) -> int:
    """Calculate leave days based on industry standards"""
    if leave_type == 'sick':
        # Sick leave includes weekends
        return (end_date - start_date).days + 1
    else:
        # Annual/casual leave excludes weekends
        days = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday=0, Sunday=6
                days += 1
            current_date += timedelta(days=1)
        return days

class LeaveRequest(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    reason: str
    
    @field_validator('leave_type')
    @classmethod
    def validate_leave_type(cls, v):
        if v not in LEAVE_TYPES:
            raise ValueError(f'Leave type must be one of: {LEAVE_TYPES}')
        return v

class LeaveApproval(BaseModel):
    status: str
    comments: Optional[str] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in ['approved', 'rejected']:
            raise ValueError('Status must be approved or rejected')
        return v

class AssignLeaveRequest(BaseModel):
    username: str
    leave_type: str
    start_date: date
    end_date: date
    reason: str
    
    @field_validator('leave_type')
    @classmethod
    def validate_leave_type(cls, v):
        if v not in LEAVE_TYPES:
            raise ValueError(f'Leave type must be one of: {LEAVE_TYPES}')
        return v

class AllocateBalanceRequest(BaseModel):
    username: str
    annual_leave: Optional[int] = None
    sick_leave: Optional[int] = None
    casual_leave: Optional[int] = None

# API: Apply for leave - Allows authenticated users to submit leave requests
# Validates dates, checks balance, prevents overlapping leaves, creates pending request
@router.post("/leaves/apply")
def apply_leave(leave_request: LeaveRequest, user_info: dict = Depends(get_user_info)):
    logger.info(f"[ENTRY] Apply leave API called by: {user_info['username']}")
    
    try:
        # Validation checks
        if leave_request.start_date > leave_request.end_date:
            raise HTTPException(status_code=400, detail={
                "error": "INVALID_DATE_RANGE",
                "message": "Start date cannot be after end date",
                "code": "LEAVE_400"
            })
        
        if not leave_request.reason.strip():
            raise HTTPException(status_code=400, detail={
                "error": "REASON_REQUIRED",
                "message": "Leave reason is required",
                "code": "LEAVE_400"
            })
        
        # Calculate days based on leave type
        days = calculate_leave_days(leave_request.start_date, leave_request.end_date, leave_request.leave_type)
        
        if days <= 0:
            raise HTTPException(status_code=400, detail={
                "error": "INVALID_DURATION",
                "message": "Leave duration must be at least 1 day",
                "code": "LEAVE_400"
            })
        
        db = get_database()

        # Check for pending leaves - block new applications if any pending leaves exist
        existing_leaves = db.leave.get_user_leaves(user_info['username'])
        pending_leaves = [leave for leave in existing_leaves if leave.get('status') == 'pending']
        
        if pending_leaves:
            raise HTTPException(status_code=400, detail={
                "error": "PENDING_LEAVE_EXISTS",
                "message": "Cannot apply for new leave while you have pending leave requests awaiting approval",
                "code": "LEAVE_400"
            })
        
        # Check for overlapping leaves with approved leaves only
        for existing_leave in existing_leaves:
            if existing_leave.get('status') == 'approved':
                existing_start = datetime.strptime(existing_leave['start_date'], '%Y-%m-%d').date() if isinstance(existing_leave['start_date'], str) else existing_leave['start_date']
                existing_end = datetime.strptime(existing_leave['end_date'], '%Y-%m-%d').date() if isinstance(existing_leave['end_date'], str) else existing_leave['end_date']
                
                if (leave_request.start_date <= existing_end and leave_request.end_date >= existing_start):
                    raise HTTPException(status_code=409, detail={
                        "error": "OVERLAPPING_LEAVE",
                        "message": "Leave dates overlap with existing approved leave",
                        "code": "LEAVE_409"
                    })
        
        # Check leave balance
        balance_data = db.leave.get_leave_balance(user_info['username'])
        logger.info(f"Balance data: {balance_data}")
        if not balance_data:
            # Create initial balance
            db.leave.create_leave_balance(user_info['username'])
            balance_data = db.leave.get_leave_balance(user_info['username'])
        
        # Check if sufficient balance
        balance_field = f"{leave_request.leave_type}_leave"
        current_balance = balance_data.get(balance_field, 0)
        
        # Since no pending leaves exist, available balance is current balance
        available_balance = current_balance
        
        if available_balance < days:
            raise HTTPException(status_code=400, detail={
                "error": "INSUFFICIENT_BALANCE",
                "message": f"Insufficient {leave_request.leave_type} leave balance. Leaves Available: {available_balance}, Leaves Applied: {days}",
                "code": "LEAVE_400"
            })
        
        # Create leave request
        leave_data = {
            "username": user_info['username'],
            "leave_type": leave_request.leave_type,
            "start_date": leave_request.start_date,
            "end_date": leave_request.end_date,
            "days": days,
            "reason": leave_request.reason,
            "status": "pending"
        }
        
        leave_id = db.leave.create_leave(leave_data)
        
        logger.info(f"[EXIT] Apply leave API successful for: {user_info['username']}")
        return success_response({"leave_id": leave_id}, "Leave application submitted successfully")
        
    except HTTPException as e:
        logger.error(f"[ERROR] Apply leave API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "apply leave")

# API: Leave dashboard - Returns user's leave history, current balance, and pending requests
# Shows remaining balance after deducting approved leaves
@router.get("/leaves/dashboard")
def get_leave_dashboard(user_info: dict = Depends(get_user_info)):
    logger.info(f"[ENTRY] Leave dashboard API called by: {user_info['username']}")
    
    try:
        db = get_database()
        
        # Get user's leaves
        leaves_data = db.leave.get_user_leaves(user_info['username'])
        leaves = leaves_data
        
        # Get leave balance
        balance_data = db.leave.get_leave_balance(user_info['username'])
        if not balance_data:
            db.leave.create_leave_balance(user_info['username'])
            balance_data = db.leave.get_leave_balance(user_info['username'])
        balance = balance_data
        
        # Calculate used leaves
        approved_leaves = [leave for leave in leaves if leave['status'] == 'approved']
        used_annual = sum(leave['days'] for leave in approved_leaves if leave['leave_type'] == 'annual')
        used_sick = sum(leave['days'] for leave in approved_leaves if leave['leave_type'] == 'sick')
        used_casual = sum(leave['days'] for leave in approved_leaves if leave['leave_type'] == 'casual')
        
        dashboard = {
            "leaves": [{
                "id": leave['id'],
                "leave_type": leave['leave_type'],
                "start_date": leave['start_date'] if isinstance(leave['start_date'], str) else leave['start_date'].isoformat(),
                "end_date": leave['end_date'] if isinstance(leave['end_date'], str) else leave['end_date'].isoformat(),
                "days": leave['days'],
                "reason": leave['reason'],
                "status": leave['status'],
                "approver_comments": leave.get('approver_comments'),
                "created_date": leave['created_date'] if isinstance(leave['created_date'], str) else leave['created_date'].isoformat()
            } for leave in leaves],
            "balance": {
                "annual_leave": balance['annual_leave'] - used_annual,
                "sick_leave": balance['sick_leave'] - used_sick,
                "casual_leave": balance['casual_leave'] - used_casual,
                "total_annual": balance['annual_leave'],
                "total_sick": balance['sick_leave'],
                "total_casual": balance['casual_leave']
            },
            "pending_approval": {
                "annual": len([leave for leave in leaves if leave['status'] == 'pending' and leave['leave_type'] == 'annual']),
                "sick": len([leave for leave in leaves if leave['status'] == 'pending' and leave['leave_type'] == 'sick']),
                "casual": len([leave for leave in leaves if leave['status'] == 'pending' and leave['leave_type'] == 'casual'])
            }
        }
        
        logger.info(f"[EXIT] Leave dashboard API successful for: {user_info['username']}")
        return success_response(dashboard, "Leave dashboard retrieved successfully")
        
    except Exception as e:
        handle_error(e, "get leave dashboard")

# API: Get pending leaves - Returns all pending leave requests for HR/Lead approval
# Requires HR or Lead role permissions
@router.get("/leaves/pending")
def get_pending_leaves(user_info: dict = Depends(require_hr)):
    logger.info(f"[ENTRY] Pending leaves API called by: {user_info['username']}")
    
    try:
        db = get_database()
        pending_leaves_data = db.leave.get_pending_leaves()
        pending_leaves = pending_leaves_data
        
        leaves_data = [{
            "id": leave.id,
            "username": leave.username,
            "annual_leave": leave.annual_leave,
            "sick_leave": leave.sick_leave,
            "casual_leave": leave.casual_leave,
            "year": leave.year
        } for leave in pending_leaves]
        
        return success_response(leaves_data, "Pending leaves retrieved successfully")
        
    except Exception as e:
        handle_error(e, "get pending leaves")

# API: Get all leaves - Returns complete leave history across all users
# Requires Lead or HR role for system-wide leave visibility
@router.get("/leaves/all")
def get_all_leaves(user_info: dict = Depends(require_leave_management)):
    logger.info(f"[ENTRY] All leaves API called by: {user_info['username']}")
    
    try:
        db = get_database()
        all_leaves_data = db.leave.get_all_leaves()
        all_leaves = all_leaves_data
        
        leaves_data = [{
            "id": leave.id,
            "username": leave.username,
            "leave_type": leave.leave_type,
            "start_date": leave.start_date if isinstance(leave.start_date, str) else leave.start_date.isoformat(),
            "end_date": leave.end_date if isinstance(leave.end_date, str) else leave.end_date.isoformat(),
            "days": leave.days,
            "reason": leave.reason,
            "status": leave.status,
            "approver_username": getattr(leave, 'approver_username', None),
            "approver_comments": getattr(leave, 'approver_comments', None),
            "created_date": leave.created_date if isinstance(leave.created_date, str) else leave.created_date.isoformat()
        } for leave in all_leaves]
        
        return success_response(leaves_data, "All leaves retrieved successfully")
        
    except Exception as e:
        handle_error(e, "get all leaves")

# API: Approve/Reject leave - Processes pending leave requests with approval/rejection
# Updates leave status, deducts balance if approved, requires Lead/HR role
@router.put("/leaves/{leave_id}/approve")
def approve_reject_leave(leave_id: int, approval: LeaveApproval, user_info: dict = Depends(require_leave_management)):
    logger.info(f"[ENTRY] Approve/Reject leave API called by: {user_info['username']} for leave: {leave_id}")
    
    try:
        db = get_database()
        
        # Get leave details
        leave_data = db.leave.get_leave_by_id(leave_id)
        if not leave_data:
            raise HTTPException(status_code=404, detail={
                "error": "LEAVE_NOT_FOUND",
                "message": "Leave not found",
                "code": "LEAVE_404"
            })
        
        leave = leave_data
        
        if leave['status'] != 'pending':
            raise HTTPException(status_code=400, detail={
                "error": "LEAVE_ALREADY_PROCESSED",
                "message": "Leave has already been processed",
                "code": "LEAVE_400"
            })
        
        # Update leave status
        update_data = {
            "status": approval.status,
            "approver_username": user_info['username'],
            "approver_comments": approval.comments,
            "approved_date": datetime.now()
        }

        logger.info(f"Updating leave {leave_id} with data: {update_data}")
        
        db.leave.update_leave(leave_id, update_data)

        # Read record from DB and show the result
        leave = db.leave.get_leave_by_id(leave_id)
        logger.info(f"Leave after update: {leave}")
        
        # If approved, deduct from leave balance
        if approval.status == 'approved':
            balance_data = db.leave.get_leave_balance(leave['username'])
            if balance_data:
                balance_field = f"{leave['leave_type']}_leave"
                current_balance = balance_data.get(balance_field, 0)
                new_balance = current_balance - leave['days']
                
                db.leave.update_leave_balance(leave['username'], {balance_field: new_balance})
        
        logger.info(f"[EXIT] Approve/Reject leave API successful for leave: {leave_id}")
        return success_response({"leave_id": leave_id}, f"Leave {approval.status} successfully")
        
    except HTTPException as e:
        logger.error(f"[ERROR] Approve/Reject leave API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "approve/reject leave")

# API: Assign leave - HR can directly assign approved leave to any user
# Bypasses approval process, immediately deducts from balance
@router.post("/leaves/assign")
def assign_leave(assign_request: AssignLeaveRequest, user_info: dict = Depends(require_hr)):
    logger.info(f"[ENTRY] Assign leave API called by: {user_info['username']} for user: {assign_request.username}")
    
    try:
        # Validate if user exists in Cognito
        validate_cognito_user(assign_request.username)
        
        db = get_database()
        
        # Calculate days based on leave type
        days = calculate_leave_days(assign_request.start_date, assign_request.end_date, assign_request.leave_type)
        
        # Create leave request directly as approved
        leave_data = {
            "username": assign_request.username,
            "leave_type": assign_request.leave_type,
            "start_date": assign_request.start_date,
            "end_date": assign_request.end_date,
            "days": days,
            "reason": assign_request.reason,
            "status": "approved",
            "approver_username": user_info['username'],
            "approver_comments": "Assigned by HR",
            "approved_date": datetime.now()
        }
        
        leave_id = db.leave.create_leave(leave_data)
        
        # Deduct from leave balance
        balance_data = db.leave.get_leave_balance(assign_request.username)
        if not balance_data:
            db.leave.create_leave_balance(assign_request.username)
            balance_data = db.leave.get_leave_balance(assign_request.username)
        
        balance = balance_data
        balance_field = f"{assign_request.leave_type}_leave"
        current_balance = getattr(balance, balance_field, 0)
        new_balance = current_balance - days
        
        db.leave.update_leave_balance(assign_request.username, {balance_field: new_balance})
        
        logger.info(f"[EXIT] Assign leave API successful for user: {assign_request.username}")
        return success_response({"leave_id": leave_id}, "Leave assigned successfully")
        
    except Exception as e:
        handle_error(e, "assign leave")

# API: Allocate leave balance - HR can set/update leave balances for users
# Creates balance record if doesn't exist, updates specified leave types
@router.post("/leaves/allocate-balance")
def allocate_leave_balance(allocate_request: AllocateBalanceRequest, user_info: dict = Depends(require_hr)):
    logger.info(f"[ENTRY] Allocate balance API called by: {user_info['username']} for user: {allocate_request.username}")
    
    try:
        # Validate if user exists in Cognito
        validate_cognito_user(allocate_request.username)
        
        db = get_database()
        
        # Get or create balance record
        balance = db.leave.get_leave_balance(allocate_request.username)
        if not balance:
            db.leave.create_leave_balance(allocate_request.username)
        
        # Update balance with provided values
        update_data = {}
        if allocate_request.annual_leave is not None:
            update_data["annual_leave"] = allocate_request.annual_leave
        if allocate_request.sick_leave is not None:
            update_data["sick_leave"] = allocate_request.sick_leave
        if allocate_request.casual_leave is not None:
            update_data["casual_leave"] = allocate_request.casual_leave
        
        if update_data:
            db.leave.update_leave_balance(allocate_request.username, update_data)
        
        logger.info(f"[EXIT] Allocate balance API successful for user: {allocate_request.username}")
        return success_response(update_data, "Leave balance allocated successfully")
        
    except HTTPException as e:
        logger.error(f"[ERROR] Allocate balance API failed: {e.detail}")
        raise
    except Exception as e:
        handle_error(e, "allocate leave balance")