#!/usr/bin/env python3
"""
Script to add mandatory and optional holidays to the database
Works with both SQLite and DynamoDB
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.db.database_factory import get_database
from scripts.db.config import USE_DYNAMODB
from datetime import date

def add_holidays_sqlite(db):
    # Get active financial year
    active_fy = db.financial_year.get_active_financial_year()
    if not active_fy:
        print("No active financial year found. Please create one first.")
        return
    
    financial_year_id = active_fy['id']
    print(f"Adding holidays for Financial Year: {active_fy['year']}")
    
    holidays = get_holiday_data()
    
    # Add mandatory holidays
    for name, holiday_date in holidays['mandatory']:
        existing_holidays = db.holiday.get_holidays_by_year(financial_year_id)
        existing = any(h['name'] == name for h in existing_holidays)
        
        if not existing:
            db.holiday.create_holiday(financial_year_id, name, holiday_date, is_mandatory=True)
            print(f"Added mandatory holiday: {name} on {holiday_date}")
        else:
            print(f"Mandatory holiday already exists: {name}")
    
    # Add optional holidays
    for name, holiday_date in holidays['optional']:
        existing_holidays = db.holiday.get_holidays_by_year(financial_year_id)
        existing = any(h['name'] == name for h in existing_holidays)
        
        if not existing:
            db.holiday.create_holiday(financial_year_id, name, holiday_date, is_mandatory=False)
            print(f"Added optional holiday: {name} on {holiday_date}")
        else:
            print(f"Optional holiday already exists: {name}")
    
    print("All holidays added successfully!")

def add_holidays_dynamodb(db):
    # Get active financial year
    active_fy = db.financial_year.get_active_financial_year()
    if not active_fy:
        print("No active financial year found. Please create one first.")
        return
    
    financial_year_id = active_fy['id']
    print(f"Adding holidays for Financial Year: {active_fy['year']}")
    
    holidays = get_holiday_data()
    
    # Add mandatory holidays
    for name, holiday_date in holidays['mandatory']:
        existing_holidays = db.holiday.get_holidays_by_year(financial_year_id)
        existing = any(h['name'] == name for h in existing_holidays)
        
        if not existing:
            db.holiday.create_holiday(financial_year_id, name, holiday_date, is_mandatory=True)
            print(f"Added mandatory holiday: {name} on {holiday_date}")
        else:
            print(f"Mandatory holiday already exists: {name}")
    
    # Add optional holidays
    for name, holiday_date in holidays['optional']:
        existing_holidays = db.holiday.get_holidays_by_year(financial_year_id)
        existing = any(h['name'] == name for h in existing_holidays)
        
        if not existing:
            db.holiday.create_holiday(financial_year_id, name, holiday_date, is_mandatory=False)
            print(f"Added optional holiday: {name} on {holiday_date}")
        else:
            print(f"Optional holiday already exists: {name}")
    
    print("All holidays added successfully!")

def get_holiday_data():
    return {
        'mandatory': [
            ("Republic Day", date(2025, 1, 26)),
            ("Independence Day", date(2024, 8, 15)),
            ("Gandhi Jayanti", date(2024, 10, 2)),
            ("Diwali", date(2024, 11, 1)),
            ("Holi", date(2025, 3, 14)),
            ("Dussehra", date(2024, 10, 12)),
            ("Eid ul-Fitr", date(2024, 4, 11)),
            ("Christmas Day", date(2024, 12, 25))
        ],
        'optional': [
            ("Good Friday", date(2025, 4, 18)),
            ("Eid ul-Adha", date(2024, 6, 17)),
            ("Karva Chauth", date(2024, 10, 20)),
            ("Bhai Dooj", date(2024, 11, 3)),
            ("Makar Sankranti", date(2025, 1, 14)),
            ("Maha Shivratri", date(2025, 2, 26)),
            ("Ram Navami", date(2025, 4, 6)),
            ("Janmashtami", date(2024, 8, 26))
        ]
    }

def add_holidays():
    db = get_database()
    
    if USE_DYNAMODB:
        add_holidays_dynamodb(db)
    else:
        add_holidays_sqlite(db)

if __name__ == "__main__":
    add_holidays()