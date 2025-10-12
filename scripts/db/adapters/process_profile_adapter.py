from typing import Optional, Dict, Any
from .base_adapter import BaseAdapter
from ..models import ProcessProfile

class ProcessProfileAdapter(BaseAdapter):
    def create_process_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        with self._db_session() as db:
            existing = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == profile_data['requirement_id'],
                ProcessProfile.recruiter_name == profile_data['recruiter_name']
            ).first()
            if existing:
                if existing.actively_working != profile_data.get('actively_working', 'No'):
                    existing.actively_working = profile_data.get('actively_working', 'No')
                    db.commit()
                return self._to_dict(existing)
        
        return self._create_record(ProcessProfile, **profile_data)
    
    def upsert_process_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        with self._db_session() as db:
            existing = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == profile_data['requirement_id'],
                ProcessProfile.profile_id == profile_data['profile_id']
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
    
    def update_process_profile_status(self, requirement_id: int, profile_id: int, status: int) -> bool:
        with self._db_session() as db:
            result = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == requirement_id,
                ProcessProfile.profile_id == profile_id
            ).update({ProcessProfile.status: status})
            db.commit()
            return result > 0
    
    def update_process_profile_remarks(self, requirement_id: int, profile_id: int, remarks: Optional[str] = None) -> bool:
        with self._db_session() as db:
            result = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == requirement_id,
                ProcessProfile.profile_id == profile_id
            ).update({ProcessProfile.remarks: remarks})
            db.commit()
            return result > 0
    
    def update_actively_working(self, requirement_id: int, profile_id: int, actively_working: str) -> bool:
        with self._db_session() as db:
            result = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == requirement_id,
                ProcessProfile.profile_id == profile_id
            ).update({ProcessProfile.actively_working: actively_working})
            db.commit()
            return result > 0
    
    def update_actively_working_by_recruiter(self, requirement_id: int, recruiter_name: str, actively_working: str) -> bool:
        with self._db_session() as db:
            result = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == requirement_id,
                ProcessProfile.recruiter_name == recruiter_name
            ).update({ProcessProfile.actively_working: actively_working})
            db.commit()
            return result > 0
    
    def update_process_profile_profile(self, requirement_id: int, profile_id: int) -> bool:
        with self._db_session() as db:
            result = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == requirement_id
            ).update({ProcessProfile.profile_id: profile_id})
            db.commit()
            return result > 0
    
    def get_profiles_by_requirement(self, requirement_id: int) -> list:
        with self._db_session() as db:
            profiles = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == requirement_id,
                ProcessProfile.profile_id != None
            ).all()
            return [self._to_dict(profile) for profile in profiles]
    
    def get_active_profiles_by_requirement(self, requirement_id: int) -> list:
        with self._db_session() as db:
            profiles = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == requirement_id,
                ProcessProfile.actively_working == 'Yes'
            ).all()
            return [self._to_dict(profile) for profile in profiles]
    
    def get_profiles_by_requirement_and_recruiter(self, requirement_id: int, recruiter_name: str) -> list:
        with self._db_session() as db:
            profiles = db.query(ProcessProfile).filter(
                ProcessProfile.requirement_id == requirement_id,
                ProcessProfile.recruiter_name == recruiter_name,
                ProcessProfile.profile_id != None
            ).all()
            return [self._to_dict(profile) for profile in profiles]