from typing import Optional, List, Dict, Any
from scripts.db.models import Requirement, RequirementStatus
from .base_adapter import BaseAdapter

class RequirementAdapter(BaseAdapter):
    def create_requirement(self, requirement_data: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def list_requirement_statuses(self) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            statuses = db.query(RequirementStatus).all()
            return [self._to_dict(status) for status in statuses]