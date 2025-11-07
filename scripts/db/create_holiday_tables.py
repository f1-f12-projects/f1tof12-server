#!/usr/bin/env python3
"""
Create holiday and financial year tables
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# ruff: noqa: E402
from scripts.db.database import engine
from scripts.db.models import FinancialYear, HolidayCalendar, UserHolidaySelection

def create_holiday_tables():
    """Create the holiday and financial year tables"""
    try:
        # Create tables
        FinancialYear.__table__.create(engine, checkfirst=True)
        HolidayCalendar.__table__.create(engine, checkfirst=True)
        UserHolidaySelection.__table__.create(engine, checkfirst=True)
        
        print("Holiday and financial year tables created successfully!")
        
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    create_holiday_tables()