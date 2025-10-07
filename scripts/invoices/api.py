from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from scripts.db.database_factory import get_database
from pydantic import BaseModel, field_validator
from datetime import date
from typing import Optional
from scripts.utils.response import success_response, handle_error
from auth import require_finance_or_manager

router = APIRouter(prefix="/invoices", tags=["invoices"])

class InvoiceCreate(BaseModel):
    invoice_number: str
    reference: Optional[str] = None
    company_id: int
    po_number: Optional[str] = None
    amount: float
    raised_date: date
    due_date: date
    status: str = "pending"
    remarks: Optional[str] = None

class InvoiceStatusUpdate(BaseModel):
    status: str
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['paid', 'pending', 'cancelled', 'overdue']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return v

class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    reference: Optional[str]
    company_id: int
    po_number: Optional[str]
    amount: float
    raised_date: date
    due_date: date
    status: str
    remarks: Optional[str]

    class Config:
        from_attributes = True

@router.post("/create")
def create_invoice(invoice: InvoiceCreate, user_info: dict = Depends(require_finance_or_manager)):
    try:
        db = get_database()
        invoice_data = db.invoice.create_invoice(invoice.dict())
        return success_response(invoice_data, "Invoice created successfully")
    except Exception as e:
        handle_error(e, "create invoice")

@router.get("/list")
def get_invoices(user_info: dict = Depends(require_finance_or_manager)):
    try:
        db = get_database()
        invoices_data = db.invoice.list_invoices()
        return success_response(invoices_data, "Invoices retrieved successfully")
    except Exception as e:
        handle_error(e, "get invoices")

@router.get("/{invoice_id}/fetch")
def get_invoice(invoice_id: int, user_info: dict = Depends(require_finance_or_manager)):
    try:
        db = get_database()
        invoice = db.invoice.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail={
                "error": "INVOICE_NOT_FOUND",
                "message": "Invoice not found",
                "code": "INV_404"
            })
        return success_response(invoice, "Invoice retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "get invoice")

@router.put("/{invoice_id}/update")
def update_invoice(invoice_id: int, status_update: InvoiceStatusUpdate, user_info: dict = Depends(require_finance_or_manager)):
    try:
        db = get_database()
        success = db.invoice.update_invoice(invoice_id, {"status": status_update.status})
        if not success:
            raise HTTPException(status_code=404, detail={
                "error": "INVOICE_NOT_FOUND",
                "message": "Invoice not found",
                "code": "INV_404"
            })
        
        updated_invoice = db.invoice.get_invoice(invoice_id)
        return success_response(updated_invoice, "Invoice status updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "update invoice")
