#!/usr/bin/env python3
"""
Migration script to alter requirements table:
1. Change date_created from DATE to DATETIME
2. Change date_closed from DATE to DATETIME  
3. Add updated_date DATETIME column
"""

import sqlite3
from datetime import datetime

def migrate_requirements_table():
    # Connect to the database
    conn = sqlite3.connect('f1tof12.db')
    cursor = conn.cursor()
    
    try:
        # Create new table with updated schema
        cursor.execute('''
            CREATE TABLE requirements_new (
                requirement_id INTEGER PRIMARY KEY,
                date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                account_id INTEGER,
                key_skill TEXT,
                jd TEXT,
                status_id INTEGER,
                recruiter_name TEXT,
                date_closed DATETIME,
                budget REAL,
                expected_billing_date DATE,
                remarks TEXT,
                req_cust_ref_id TEXT,
                updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES companies (id),
                FOREIGN KEY (status_id) REFERENCES requirement_status (id)
            )
        ''')
        
        # Copy data from old table to new table
        cursor.execute('''
            INSERT INTO requirements_new (
                requirement_id, date_created, account_id, key_skill, jd, 
                status_id, recruiter_name, date_closed, budget, 
                expected_billing_date, remarks, req_cust_ref_id, updated_date
            )
            SELECT 
                requirement_id, 
                datetime(date_created) as date_created,
                account_id, key_skill, jd, status_id, recruiter_name,
                datetime(date_closed) as date_closed,
                budget, expected_billing_date, remarks, req_cust_ref_id,
                CURRENT_TIMESTAMP as updated_date
            FROM requirements
        ''')
        
        # Drop old table
        cursor.execute('DROP TABLE requirements')
        
        # Rename new table
        cursor.execute('ALTER TABLE requirements_new RENAME TO requirements')
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_requirements_table()