#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Test DynamoDB connection
load_dotenv('.env.server')
os.environ['USE_DYNAMODB'] = 'true'

from scripts.db.database_factory import get_database

def test_connection():
    try:
        db = get_database()
        print("✅ DynamoDB connection successful")
        
        # Test operations
        companies = db.list_companies()
        print(f"📋 Found {len(companies)} companies")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_connection()