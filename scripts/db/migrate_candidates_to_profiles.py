#!/usr/bin/env python3
"""
Migration script to rename candidates table to profiles
"""
import sqlite3
import os
import sys
sys.path.append('.')
from scripts.db.config import DB_FILE_NAME

def migrate_sqlite():
    """Migrate SQLite database from candidates to profiles"""
    if not os.path.exists(DB_FILE_NAME):
        print(f"Database file {DB_FILE_NAME} not found. Skipping migration.")
        return
    
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()
    
    try:
        # Check if candidates table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='candidates'")
        if not cursor.fetchone():
            print("Candidates table not found. Migration may have already been completed.")
            conn.close()
            return
        
        # Rename candidates table to profiles
        cursor.execute("ALTER TABLE candidates RENAME TO profiles")
        print("Renamed candidates table to profiles")
        
        # Rename candidate_status table to profile_status
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='candidate_status'")
        if cursor.fetchone():
            cursor.execute("ALTER TABLE candidate_status RENAME TO profile_status")
            print("Renamed candidate_status table to profile_status")
        
        # Update process_profiles table to use profile_id instead of candidate_id
        cursor.execute("PRAGMA table_info(process_profiles)")
        columns = cursor.fetchall()
        has_candidate_id = any(col[1] == 'candidate_id' for col in columns)
        
        if has_candidate_id:
            # Create new table with updated schema
            cursor.execute("""
                CREATE TABLE process_profiles_new (
                    id INTEGER PRIMARY KEY,
                    requirement_id INTEGER,
                    recruiter_name TEXT,
                    profile_id INTEGER,
                    status INTEGER,
                    remarks TEXT,
                    FOREIGN KEY (requirement_id) REFERENCES requirements (requirement_id),
                    FOREIGN KEY (profile_id) REFERENCES profiles (id)
                )
            """)
            
            # Copy data from old table to new table
            cursor.execute("""
                INSERT INTO process_profiles_new (id, requirement_id, recruiter_name, profile_id, status, remarks)
                SELECT id, requirement_id, recruiter_name, candidate_id, status, remarks
                FROM process_profiles
            """)
            
            # Drop old table and rename new table
            cursor.execute("DROP TABLE process_profiles")
            cursor.execute("ALTER TABLE process_profiles_new RENAME TO process_profiles")
            print("Updated process_profiles table to use profile_id")
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_sqlite()