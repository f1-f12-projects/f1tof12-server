from typing import Optional, List, Dict, Any, Type
from sqlalchemy.orm import Session
from sqlalchemy import func
from contextlib import contextmanager
from scripts.db.database import get_db
from scripts.db.models import User, Company, Invoice, SPOC, Requirement
from scripts.db.database_factory import DatabaseInterface

class SQLiteAdapter(DatabaseInterface):
    @contextmanager
    def _db_session(self):
        db = next(get_db())
        try:
            yield db
        finally:
            db.close()
    
    def _to_dict(self, obj, date_fields: Optional[List[str]] = None, datetime_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        result = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        if date_fields:
            for field in date_fields:
                if result.get(field):
                    result[field] = result[field].strftime('%Y-%m-%d')
        if datetime_fields:
            for field in datetime_fields:
                if result.get(field):
                    result[field] = result[field].isoformat()
        return result
    
    def _create_record(self, model_class: Type, **kwargs) -> Dict[str, Any]:
        with self._db_session() as db:
            record = model_class(**kwargs)
            db.add(record)
            db.commit()
            return self._to_dict(record)
    
    def _update_record(self, model_class: Type, record_id: int, update_data: Dict[str, Any]) -> bool:
        with self._db_session() as db:
            column_updates = {getattr(model_class, key): value for key, value in update_data.items()}
            result = db.query(model_class).filter(model_class.id == record_id).update(column_updates)
            db.commit()
            return result > 0
    
    def create_user(self, username: str, hashed_password: str) -> Dict[str, Any]:
        result = self._create_record(User, username=username, hashed_password=hashed_password)
        return {"id": result["id"], "username": result["username"]}
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        with self._db_session() as db:
            user = db.query(User).filter(User.username == username).first()
            return self._to_dict(user) if user else None
    
    def create_company(self, name: str, spoc: str, email_id: str, status: str = "active") -> Dict[str, Any]:
        return self._create_record(Company, name=name, spoc=spoc, email_id=email_id, status=status)
    
    def get_company_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        with self._db_session() as db:
            company = db.query(Company).filter(func.lower(Company.name) == func.lower(name)).first()
            return self._to_dict(company) if company else None
    
    def list_companies(self) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            companies = db.query(Company).all()
            return [self._to_dict(company) for company in companies]
    
    def update_company(self, company_id: int, update_data: Dict[str, Any]) -> bool:
        return self._update_record(Company, company_id, update_data)
    
    def create_spoc(self, company_id: int, name: str, phone: str, email_id: str, location: str, status: str = "active") -> Dict[str, Any]:
        return self._create_record(SPOC, company_id=company_id, name=name, phone=phone, email_id=email_id, location=location, status=status)
    
    def list_spocs(self) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            spocs = db.query(SPOC).all()
            return [self._to_dict(spoc) for spoc in spocs]
    
    def update_spoc(self, spoc_id: int, update_data: Dict[str, Any]) -> bool:
        return self._update_record(SPOC, spoc_id, update_data)
    
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
    
    def create_requirement(self, requirement_data: Dict[str, Any]) -> Dict[str, Any]:
        # Filter None values and create record
        return self._create_record(Requirement, **{k: v for k, v in requirement_data.items() if v is not None})
    
    def list_requirements(self) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            requirements = db.query(Requirement).all()
            return [self._to_dict(req, ['expected_billing_date'], ['created_date', 'closed_date', 'updated_date']) for req in requirements]
    
    def get_requirement(self, requirement_id: int) -> Optional[Dict[str, Any]]:
        with self._db_session() as db:
            requirement = db.query(Requirement).filter(Requirement.requirement_id == requirement_id).first()
            return self._to_dict(requirement, ['expected_billing_date'], ['created_date', 'closed_date', 'updated_date']) if requirement else None
    
    def update_requirement(self, requirement_id: int, update_data: Dict[str, Any]) -> bool:
        # Map API fields to database columns
        field_mapping = {
            'company_id': 'company_id',
            'skills_required': 'key_skill',
            'description': 'jd',
            'expected_billing_date': 'expected_billing_date',
            'created_date': 'created_date'
        }
        
        mapped_data = {}
        for api_field, value in update_data.items():
            db_field = field_mapping.get(api_field, api_field)
            mapped_data[db_field] = value
        
        with self._db_session() as db:
            column_updates = {getattr(Requirement, key): value for key, value in mapped_data.items()}
            result = db.query(Requirement).filter(Requirement.requirement_id == requirement_id).update(column_updates)
            db.commit()
            return result > 0