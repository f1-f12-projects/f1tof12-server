from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from scripts.db.database import get_db, Invoice, User
from pydantic import BaseModel, field_validator
from datetime import date
from typing import Optional
from auth import verify_cognito_token
from scripts.utils.response import success_response, handle_error

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
def create_invoice(invoice: InvoiceCreate, current_user: User = Depends(verify_cognito_token), db: Session = Depends(get_db)):
    try:
        db_invoice = Invoice(**invoice.dict())
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
        return success_response(db_invoice.__dict__, "Invoice created successfully")
    except Exception as e:
        handle_error(e, "create invoice")

@router.get("/list")
def get_invoices(current_user: User = Depends(verify_cognito_token), db: Session = Depends(get_db)):
    try:
        invoices = db.query(Invoice).all()
        invoices_data = [invoice.__dict__ for invoice in invoices]
        return success_response(invoices_data, "Invoices retrieved successfully")
    except Exception as e:
        handle_error(e, "get invoices")

@router.get("/{invoice_id}/fetch")
def get_invoice(invoice_id: int, current_user: User = Depends(verify_cognito_token), db: Session = Depends(get_db)):
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail={
                "error": "INVOICE_NOT_FOUND",
                "message": "Invoice not found",
                "code": "INV_404"
            })
        return success_response(invoice.__dict__, "Invoice retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "get invoice")

@router.put("/{invoice_id}/update")
def update_invoice(invoice_id: int, status_update: InvoiceStatusUpdate, current_user: User = Depends(verify_cognito_token), db: Session = Depends(get_db)):
    try:
        db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not db_invoice:
            raise HTTPException(status_code=404, detail={
                "error": "INVOICE_NOT_FOUND",
                "message": "Invoice not found",
                "code": "INV_404"
            })
        
        current_status = getattr(db_invoice, 'status', None)
        if current_status == status_update.status:
            return success_response(db_invoice.__dict__, "Invoice status unchanged")
        
        db.query(Invoice).filter(Invoice.id == invoice_id).update({"status": status_update.status})
        db.commit()
        db.refresh(db_invoice)
        return success_response(db_invoice.__dict__, "Invoice status updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "update invoice")
