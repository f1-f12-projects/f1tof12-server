from typing import Optional, List, Dict, Any
from scripts.db.models import Profile, ProfileStatus
from .base_adapter import BaseAdapter

class ProfileAdapter(BaseAdapter):
    def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._create_record(Profile, **profile_data)
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            profiles = db.query(Profile).all()
            return [self._to_dict(profile, datetime_fields=['created_date', 'updated_date']) for profile in profiles]
    
    def get_profile(self, profile_id: int) -> Optional[Dict[str, Any]]:
        with self._db_session() as db:
            profile = db.query(Profile).filter(Profile.id == profile_id).first()
            return self._to_dict(profile, datetime_fields=['created_date', 'updated_date']) if profile else None
    
    def update_profile(self, profile_id: int, update_data: Dict[str, Any]) -> bool:
        return self._update_record(Profile, profile_id, update_data)
    
    def list_profile_statuses(self) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            statuses = db.query(ProfileStatus).all()
            return [self._to_dict(status) for status in statuses]