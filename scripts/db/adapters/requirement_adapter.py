from typing import Optional, List, Dict, Any
from scripts.db.models import Requirement, RequirementStatus
from .base_adapter import BaseAdapter

class RequirementAdapter(BaseAdapter):
    def create_requirement(self, requirement_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._create_record(Requirement, **{k: v for k, v in requirement_data.items() if v is not None})
    
    def list_requirements(self) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            db.expire_all()  # Ensure fresh data from database
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
    
    def get_open_requirements_by_company(self, company_id: int) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            requirements = db.query(Requirement).filter(
                Requirement.company_id == company_id,
                Requirement.status_id.in_([1, 2, 3])  # Open statuses (not 4=Closed, 5=Fulfilled)
            ).all()
            return [self._to_dict(req, ['expected_billing_date'], ['created_date', 'closed_date', 'updated_date']) for req in requirements]
    
    def get_open_requirements_by_company_and_recruiter(self, company_id: int, recruiter_name: str) -> List[Dict[str, Any]]:
        from scripts.db.models import ProcessProfile
        with self._db_session() as db:
            requirements = db.query(Requirement).join(
                ProcessProfile, Requirement.requirement_id == ProcessProfile.requirement_id
            ).filter(
                Requirement.company_id == company_id,
                Requirement.status_id.in_([1, 2, 3]),
                ProcessProfile.recruiter_name == recruiter_name
            ).all()
            return [self._to_dict(req, ['expected_billing_date'], ['created_date', 'closed_date', 'updated_date']) for req in requirements]