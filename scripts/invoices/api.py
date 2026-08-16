from fastapi import APIRouter, Depends, HTTPException
from scripts.db.database_factory import get_database
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date
from scripts.utils.response import success_response, handle_error
from auth import require_finance_or_manager

router = APIRouter(prefix="/invoices", tags=["invoices"])

class InvoiceCreate(BaseModel):
    invoice_number: str
    reference: str | None = None
    company_id: int
    po_number: str | None = None
    amount: float
    raised_date: date
    due_date: date
    status: str = "pending"
    remarks: str | None = None

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
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    reference: str | None
    company_id: int
    po_number: str | None
    amount: float
    raised_date: date
    due_date: date
    status: str
    remarks: str | None

@router.post("/create")
def create_invoice(invoice: InvoiceCreate, user_info: dict = Depends(require_finance_or_manager)):
    try:
        db = get_database()
        invoice_data = db.invoice.create_invoice(invoice.model_dump())
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

@router.get("/list/by-date-range")
def get_invoices_by_date_range(from_date: date, to_date: date, user_info: dict = Depends(require_finance_or_manager)):
    if from_date > to_date:
        raise HTTPException(status_code=400, detail={
            "error": "INVALID_DATE_RANGE",
            "message": "from_date must be before or equal to to_date",
            "code": "INV_400"
        })
    try:
        db = get_database()
        invoices_data = db.invoice.list_invoices_by_date_range(from_date, to_date)
        return success_response(invoices_data, "Invoices retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "get invoices by date range")

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
