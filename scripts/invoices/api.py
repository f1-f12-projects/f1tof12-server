from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from scripts.db.database import get_db, Invoice, User
from pydantic import BaseModel
from datetime import date
from typing import Optional
from auth import verify_cognito_token

router = APIRouter(prefix="/invoices", tags=["invoices"])

class InvoiceCreate(BaseModel):
    invoice_number: str
    reference: Optional[str] = None
    company_id: int
    raised_date: date
    due_date: date
    status: str = "pending"
    remarks: Optional[str] = None

class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    reference: Optional[str]
    company_id: int
    raised_date: date
    due_date: date
    status: str
    remarks: Optional[str]

    class Config:
        from_attributes = True

@router.post("/", response_model=InvoiceResponse)
def create_invoice(invoice: InvoiceCreate, current_user: User = Depends(verify_cognito_token), db: Session = Depends(get_db)):
    db_invoice = Invoice(**invoice.dict())
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

@router.get("/", response_model=list[InvoiceResponse])
def get_invoices(current_user: User = Depends(verify_cognito_token), db: Session = Depends(get_db)):
    return db.query(Invoice).all()

@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int, current_user: User = Depends(verify_cognito_token), db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.put("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(invoice_id: int, invoice: InvoiceCreate, current_user: User = Depends(verify_cognito_token), db: Session = Depends(get_db)):
    db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    for key, value in invoice.dict().items():
        setattr(db_invoice, key, value)
    
    db.commit()
    db.refresh(db_invoice)
    return db_invoice
