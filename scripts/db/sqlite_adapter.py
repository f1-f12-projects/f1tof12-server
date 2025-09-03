from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from scripts.db.database import get_db
from scripts.db.models import User, Company
from scripts.db.database_factory import DatabaseInterface

class SQLiteAdapter(DatabaseInterface):
    def _get_db(self) -> Session:
        return next(get_db())
    
    def create_user(self, username: str, hashed_password: str) -> Dict[str, Any]:
        db = self._get_db()
        try:
            db_user = User(username=username, hashed_password=hashed_password)
            db.add(db_user)
            db.commit()
            return {"id": db_user.id, "username": db_user.username}
        finally:
            db.close()
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        db = self._get_db()
        try:
            user = db.query(User).filter(User.username == username).first()
            if user:
                return {"id": user.id, "username": user.username, "hashed_password": user.hashed_password}
            return None
        finally:
            db.close()
    
    def create_company(self, name: str, spoc: str, email_id: str, status: str = "active") -> Dict[str, Any]:
        db = self._get_db()
        try:
            db_company = Company(name=name, spoc=spoc, email_id=email_id, status=status)
            db.add(db_company)
            db.commit()
            return {
                "id": db_company.id,
                "name": db_company.name,
                "spoc": db_company.spoc,
                "email_id": db_company.email_id,
                "status": db_company.status,
                "created_date": db_company.created_date,
                "updated_date": db_company.updated_date
            }
        finally:
            db.close()
    
    def get_company_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        db = self._get_db()
        try:
            company = db.query(Company).filter(func.lower(Company.name) == func.lower(name)).first()
            if company:
                return {
                    "id": company.id,
                    "name": company.name,
                    "spoc": company.spoc,
                    "email_id": company.email_id,
                    "status": company.status,
                    "created_date": company.created_date,
                    "updated_date": company.updated_date
                }
            return None
        finally:
            db.close()
    
    def list_companies(self) -> List[Dict[str, Any]]:
        db = self._get_db()
        try:
            companies = db.query(Company).all()
            return [{
                "id": company.id,
                "name": company.name,
                "spoc": company.spoc,
                "email_id": company.email_id,
                "status": company.status,
                "created_date": company.created_date,
                "updated_date": company.updated_date
            } for company in companies]
        finally:
            db.close()
    
    def update_company(self, company_id: int, update_data: Dict[str, Any]) -> bool:
        db = self._get_db()
        try:
            result = db.query(Company).filter(Company.id == company_id).update(update_data)
            db.commit()
            return result > 0
        finally:
            db.close()