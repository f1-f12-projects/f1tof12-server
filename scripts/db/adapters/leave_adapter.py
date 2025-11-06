from typing import List, Dict, Any, Optional
from scripts.db.adapters.base_adapter import BaseAdapter
from scripts.db.models import Leave, LeaveBalance
from datetime import datetime

class LeaveAdapter(BaseAdapter):
    
    def create_leave(self, leave_data: Dict[str, Any]) -> int:
        with self._db_session() as db:
            leave = Leave(**leave_data)
            db.add(leave)
            db.commit()
            return leave.id
    
    def get_user_leaves(self, username: str) -> List[Leave]:
        with self._db_session() as db:
            return db.query(Leave).filter(Leave.username == username).order_by(Leave.created_date.desc()).all()
    
    def get_pending_leaves(self) -> List[Leave]:
        with self._db_session() as db:
            return db.query(Leave).filter(Leave.status == 'pending').order_by(Leave.created_date.desc()).all()
    
    def get_all_leaves(self) -> List[Leave]:
        with self._db_session() as db:
            return db.query(Leave).order_by(Leave.created_date.desc()).all()
    
    def get_leave_by_id(self, leave_id: int) -> Optional[Leave]:
        with self._db_session() as db:
            return db.query(Leave).filter(Leave.id == leave_id).first()
    
    def update_leave(self, leave_id: int, update_data: Dict[str, Any]) -> bool:
        return self._update_record(Leave, leave_id, update_data)
    
    def create_leave_balance(self, username: str) -> int:
        with self._db_session() as db:
            balance = LeaveBalance(username=username)
            db.add(balance)
            db.commit()
            return balance.id
    
    def get_leave_balance(self, username: str) -> Optional[LeaveBalance]:
        with self._db_session() as db:
            return db.query(LeaveBalance).filter(LeaveBalance.username == username).first()
    
    def update_leave_balance(self, username: str, update_data: Dict[str, Any]) -> bool:
        with self._db_session() as db:
            result = db.query(LeaveBalance).filter(LeaveBalance.username == username).update(update_data)
            db.commit()
            return result > 0