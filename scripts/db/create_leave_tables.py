#!/usr/bin/env python3
"""
Script to create leave management tables in the database
"""
import sys
import os
from scripts.db.database import engine
from scripts.db.models import Leave, LeaveBalance

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def create_leave_tables():
    """Create leave management tables"""
    try:
        # Create only the leave tables
        Leave.__table__.create(engine, checkfirst=True)
        LeaveBalance.__table__.create(engine, checkfirst=True)
        print("Leave management tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    create_leave_tables()