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
    
    def get_profiles_by_date_range(self, start_date, end_date, recruiter_name=None) -> List[Dict[str, Any]]:
        from scripts.db.models import ProcessProfile
        with self._db_session() as db:
            query = db.query(
                Profile.id.label('profile_id'),
                Profile.status,
                Profile.name,
                ProcessProfile.recruiter_name,
                ProcessProfile.requirement_id
            ).outerjoin(
                ProcessProfile, Profile.id == ProcessProfile.profile_id
            ).filter(
                Profile.created_date >= start_date,
                Profile.created_date <= end_date
            )
            
            # Filter by recruiter if provided
            if recruiter_name:
                query = query.filter(ProcessProfile.recruiter_name == recruiter_name)
            
            profiles = query.all()
            
            return [{
                'profile_id': profile.profile_id,
                'status': profile.status,
                'name': profile.name,
                'recruiter_name': profile.recruiter_name,
                'requirement_id': profile.requirement_id
            } for profile in profiles]