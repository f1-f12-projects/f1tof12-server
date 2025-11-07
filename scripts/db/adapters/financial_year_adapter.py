from typing import List, Dict, Any, Optional
from scripts.db.adapters.base_adapter import BaseAdapter
from scripts.db.models import FinancialYear

class FinancialYearAdapter(BaseAdapter):
    def create_financial_year(self, year: int, start_date, end_date, is_active: bool = False) -> int:
        with self._db_session() as db:
            # If setting as active, deactivate all others first
            if is_active:
                db.query(FinancialYear).update({"is_active": False})
            
            financial_year = FinancialYear(
                year=year,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active
            )
            db.add(financial_year)
            db.commit()
            return financial_year.id
    
    def get_all_financial_years(self) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            years = db.query(FinancialYear).order_by(FinancialYear.year.desc()).all()
            return [self._to_dict(year, date_fields=['start_date', 'end_date'], datetime_fields=['created_date', 'updated_date']) for year in years]
    
    def get_active_financial_year(self) -> Optional[Dict[str, Any]]:
        with self._db_session() as db:
            year = db.query(FinancialYear).filter(FinancialYear.is_active == True).first()
            return self._to_dict(year, date_fields=['start_date', 'end_date'], datetime_fields=['created_date', 'updated_date']) if year else None
    
    def get_financial_year_by_id(self, year_id: int) -> Optional[Dict[str, Any]]:
        with self._db_session() as db:
            year = db.query(FinancialYear).filter(FinancialYear.id == year_id).first()
            return self._to_dict(year, date_fields=['start_date', 'end_date'], datetime_fields=['created_date', 'updated_date']) if year else None
    
    def set_active_financial_year(self, year_id: int) -> bool:
        with self._db_session() as db:
            # Deactivate all years
            db.query(FinancialYear).update({"is_active": False})
            # Activate the specified year
            result = db.query(FinancialYear).filter(FinancialYear.id == year_id).update({"is_active": True})
            db.commit()
            return result > 0
    
    def update_financial_year(self, year_id: int, update_data: Dict[str, Any]) -> bool:
        with self._db_session() as db:
            # If setting as active, deactivate all others first
            if update_data.get('is_active'):
                db.query(FinancialYear).update({"is_active": False})
            
            result = db.query(FinancialYear).filter(FinancialYear.id == year_id).update(update_data)
            db.commit()
            return result > 0
    
