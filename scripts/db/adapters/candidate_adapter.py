from typing import Optional, List, Dict, Any
from scripts.db.models import Candidate, CandidateStatus
from .base_adapter import BaseAdapter

class CandidateAdapter(BaseAdapter):
    def create_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._create_record(Candidate, **candidate_data)
    
    def list_candidates(self) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            candidates = db.query(Candidate).all()
            return [self._to_dict(candidate, datetime_fields=['created_date', 'updated_date']) for candidate in candidates]
    
    def get_candidate(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        with self._db_session() as db:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            return self._to_dict(candidate, datetime_fields=['created_date', 'updated_date']) if candidate else None
    
    def update_candidate(self, candidate_id: int, update_data: Dict[str, Any]) -> bool:
        return self._update_record(Candidate, candidate_id, update_data)
    
    def list_candidate_statuses(self) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            statuses = db.query(CandidateStatus).all()
            return [self._to_dict(status) for status in statuses]