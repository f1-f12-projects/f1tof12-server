from typing import Optional, List, Dict, Any
from sqlalchemy import func
from scripts.db.models import Company
from .base_adapter import BaseAdapter

class CompanyAdapter(BaseAdapter):
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
    
    def list_active_companies(self) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            companies = db.query(Company).filter(Company.status == "active").all()
            return [self._to_dict(company) for company in companies]
    
    def update_company(self, company_id: int, update_data: Dict[str, Any]) -> bool:
        return self._update_record(Company, company_id, update_data)