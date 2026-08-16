from typing import Any
from scripts.db.models import Invoice
from .base_adapter import BaseAdapter

class InvoiceAdapter(BaseAdapter):
    def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._create_record(Invoice, **invoice_data)
    
    def list_invoices(self) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            invoices = db.query(Invoice).all()
            return [self._to_dict(invoice, ['raised_date', 'due_date']) for invoice in invoices]
    
    def get_invoice(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        with self._db_session() as db:
            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
            return self._to_dict(invoice, ['raised_date', 'due_date']) if invoice else None
    
    def update_invoice(self, invoice_id: int, update_data: Dict[str, Any]) -> bool:
        return self._update_record(Invoice, invoice_id, update_data)

    def list_invoices_by_date_range(self, from_date, to_date) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            invoices = db.query(Invoice).filter(
                Invoice.raised_date >= from_date,
                Invoice.raised_date <= to_date
            ).all()
            return [self._to_dict(invoice, ['raised_date', 'due_date']) for invoice in invoices]