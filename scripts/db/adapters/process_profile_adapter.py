from typing import Optional, Dict, Any
from scripts.db.models import ProcessProfile
from .base_adapter import BaseAdapter

class ProcessProfileAdapter(BaseAdapter):
    def create_process_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        with self._db_session() as db:
            existing = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == profile_data['requirement_id'],
                ProcessProfile.recruiter_name == profile_data['recruiter_name']
            ).first()
            if existing:
                return self._to_dict(existing)
        
        return self._create_record(ProcessProfile, **profile_data)
    
    def upsert_process_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        with self._db_session() as db:
            existing = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == profile_data['requirement_id'],
                ProcessProfile.candidate_id == profile_data['candidate_id']
            ).first()
            
            if existing:
                for key, value in profile_data.items():
                    setattr(existing, key, value)
                db.commit()
                return self._to_dict(existing)
            else:
                return self._create_record(ProcessProfile, **profile_data)
    
    def update_process_profile_recruiter(self, requirement_id: int, recruiter_name: str) -> bool:
        with self._db_session() as db:
            result = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == requirement_id
            ).update({ProcessProfile.recruiter_name: recruiter_name})
            db.commit()
            return result > 0
    
    def update_process_profile_status(self, requirement_id: int, candidate_id: int, status: int) -> bool:
        with self._db_session() as db:
            result = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == requirement_id,
                ProcessProfile.candidate_id == candidate_id
            ).update({ProcessProfile.status: status})
            db.commit()
            return result > 0
    
    def update_process_profile_remarks(self, requirement_id: int, candidate_id: int, remarks: Optional[str] = None) -> bool:
        with self._db_session() as db:
            result = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == requirement_id,
                ProcessProfile.candidate_id == candidate_id
            ).update({ProcessProfile.remarks: remarks})
            db.commit()
            return result > 0
    
    def update_process_profile_candidate(self, requirement_id: int, candidate_id: int) -> bool:
        with self._db_session() as db:
            result = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == requirement_id
            ).update({ProcessProfile.candidate_id: candidate_id})
            db.commit()
            return result > 0