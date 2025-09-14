#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

def setup_local():
    """Setup for local development with SQLite"""
    load_dotenv('.env.local')
    print("✅ Local environment configured (SQLite)")
    print(f"Database: {os.getenv('DB_FILE_NAME', 'f1tof12.db')}")

def setup_prod():
    """Setup for production deployment with DynamoDB"""
    print("✅ Production environment configured (DynamoDB)")
    print(f"Region: ap-south-1")
    print(f"Tables: Managed by CloudFormation")
    
    # Create DynamoDB tables
    try:
        from scripts.db.create_dynamodb_tables import create_dynamodb_tables
        create_dynamodb_tables()
    except Exception as e:
        print(f"⚠️  Could not create DynamoDB tables: {e}")

if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "local"
    
    if env == "local":
        setup_local()
    elif env == "prod":
        setup_prod()
    else:
        print("Usage: python setup_environment.py [local|prod]")