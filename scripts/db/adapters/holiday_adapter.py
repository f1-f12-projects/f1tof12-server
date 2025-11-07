from typing import List, Dict, Any, Optional
from scripts.db.adapters.base_adapter import BaseAdapter
from scripts.db.models import HolidayCalendar, UserHolidaySelection, FinancialYear
from sqlalchemy.orm import joinedload

class HolidayAdapter(BaseAdapter):
    def create_holiday(self, financial_year_id: int, name: str, date, is_mandatory: bool = True) -> int:
        with self._db_session() as db:
            holiday = HolidayCalendar(
                financial_year_id=financial_year_id,
                name=name,
                date=date,
                is_mandatory=is_mandatory
            )
            db.add(holiday)
            db.commit()
            return holiday.id
    
    def get_holidays_by_year(self, financial_year_id: int) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            holidays = db.query(HolidayCalendar).filter(
                HolidayCalendar.financial_year_id == financial_year_id
            ).order_by(HolidayCalendar.date).all()
            return [self._to_dict(holiday, date_fields=['date'], datetime_fields=['created_date', 'updated_date']) for holiday in holidays]
    
    def get_holiday_by_id(self, holiday_id: int) -> Optional[Dict[str, Any]]:
        with self._db_session() as db:
            holiday = db.query(HolidayCalendar).filter(HolidayCalendar.id == holiday_id).first()
            return self._to_dict(holiday, date_fields=['date'], datetime_fields=['created_date', 'updated_date']) if holiday else None
    
    def get_optional_holidays(self, financial_year_id: int) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            holidays = db.query(HolidayCalendar).filter(
                HolidayCalendar.financial_year_id == financial_year_id,
                HolidayCalendar.is_mandatory == False
            ).order_by(HolidayCalendar.date).all()
            return [self._to_dict(holiday, date_fields=['date'], datetime_fields=['created_date', 'updated_date']) for holiday in holidays]
    
    def get_mandatory_holidays(self, financial_year_id: int) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            holidays = db.query(HolidayCalendar).filter(
                HolidayCalendar.financial_year_id == financial_year_id,
                HolidayCalendar.is_mandatory == True
            ).order_by(HolidayCalendar.date).all()
            return [self._to_dict(holiday, date_fields=['date'], datetime_fields=['created_date', 'updated_date']) for holiday in holidays]
    
    def update_holiday(self, holiday_id: int, update_data: Dict[str, Any]) -> bool:
        return self._update_record(HolidayCalendar, holiday_id, update_data)
    
    def delete_holiday(self, holiday_id: int) -> bool:
        with self._db_session() as db:
            result = db.query(HolidayCalendar).filter(HolidayCalendar.id == holiday_id).delete()
            db.commit()
            return result > 0
    
    def select_optional_holidays(self, username: str, holiday_ids: List[int], financial_year_id: int) -> bool:
        with self._db_session() as db:
            # Remove existing selections for this user and year
            db.query(UserHolidaySelection).filter(
                UserHolidaySelection.username == username,
                UserHolidaySelection.financial_year_id == financial_year_id
            ).delete()
            
            # Add new selections
            for holiday_id in holiday_ids:
                selection = UserHolidaySelection(
                    username=username,
                    holiday_id=holiday_id,
                    financial_year_id=financial_year_id
                )
                db.add(selection)
            
            db.commit()
            return True
    
    def get_user_selected_holidays(self, username: str, financial_year_id: int) -> List[Dict[str, Any]]:
        with self._db_session() as db:
            selections = db.query(UserHolidaySelection).options(
                joinedload(UserHolidaySelection.holiday)
            ).filter(
                UserHolidaySelection.username == username,
                UserHolidaySelection.financial_year_id == financial_year_id
            ).all()
            
            result = []
            for selection in selections:
                holiday_dict = self._to_dict(selection.holiday, date_fields=['date'], datetime_fields=['created_date', 'updated_date'])
                holiday_dict['selection_date'] = selection.created_date.isoformat()
                result.append(holiday_dict)
            
            return result
    
    def get_user_holidays_for_year(self, username: str, financial_year_id: int) -> Dict[str, Any]:
        with self._db_session() as db:
            # Get all mandatory holidays
            mandatory = self.get_mandatory_holidays(financial_year_id)
            
            # Get user's selected optional holidays
            selected_optional = self.get_user_selected_holidays(username, financial_year_id)
            
            # Get all optional holidays to show available ones
            all_optional = self.get_optional_holidays(financial_year_id)
            
            return {
                "mandatory_holidays": mandatory,
                "selected_optional_holidays": selected_optional,
                "available_optional_holidays": all_optional
            }