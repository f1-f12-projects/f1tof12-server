from typing import Optional, Dict, Any
from scripts.db.models import User
from .base_adapter import BaseAdapter

class UserAdapter(BaseAdapter):
    def create_user(self, username: str, hashed_password: str) -> Dict[str, Any]:
        result = self._create_record(User, username=username, hashed_password=hashed_password)
        return {"id": result["id"], "username": result["username"]}
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        with self._db_session() as db:
            user = db.query(User).filter(User.username == username).first()
            return self._to_dict(user) if user else None