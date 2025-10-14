from typing import List, Dict, Any
from scripts.db.models import SPOC
from .base_adapter import BaseAdapter

class SPOCAdapter(BaseAdapter):
    def create_spoc(self, company_id: int, name: str, phone: str, email_id: str, location: str, status: str = "active") -> Dict[str, Any]:
        return self._create_record(SPOC, company_id=company_id, name=name, phone=phone, email_id=email_id, location=location, status=status)
    
    def list_spocs(self) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            spocs = db.query(SPOC).all()
            return [self._to_dict(spoc) for spoc in spocs]
    
    def update_spoc(self, spoc_id: int, update_data: Dict[str, Any]) -> bool:
        return self._update_record(SPOC, spoc_id, update_data)
    
    def get_spocs_by_company(self, company_id: int) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            spocs = db.query(SPOC).filter(SPOC.company_id == company_id, SPOC.status == "active").all()
            return [self._to_dict(spoc) for spoc in spocs]
    
