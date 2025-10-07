from typing import Optional, List, Dict, Any, Type
from sqlalchemy.orm import Session
from contextlib import contextmanager
from scripts.db.database import get_db

class BaseAdapter:
    @contextmanager
    def _db_session(self):
        db = next(get_db())
        try:
            yield db
        finally:
            db.close()
    
    def _to_dict(self, obj, date_fields: Optional[List[str]] = None, datetime_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        result = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        if date_fields:
            for field in date_fields:
                if result.get(field):
                    result[field] = result[field].strftime('%Y-%m-%d')
        if datetime_fields:
            for field in datetime_fields:
                if result.get(field):
                    result[field] = result[field].isoformat()
        return result
    
    def _create_record(self, model_class: Type, **kwargs) -> Dict[str, Any]:
        with self._db_session() as db:
            record = model_class(**kwargs)
            db.add(record)
            db.commit()
            return self._to_dict(record)
    
    def _update_record(self, model_class: Type, record_id: int, update_data: Dict[str, Any]) -> bool:
        with self._db_session() as db:
            column_updates = {getattr(model_class, key): value for key, value in update_data.items()}
            result = db.query(model_class).filter(model_class.id == record_id).update(column_updates)
            db.commit()
            return result > 0