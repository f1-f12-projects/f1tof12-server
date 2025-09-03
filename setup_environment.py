#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

def setup_local():
    """Setup for local development with SQLite"""
    load_dotenv('.env.local')
    print("✅ Local environment configured (SQLite)")
    print(f"Database: {os.getenv('DB_FILE_NAME', 'f1tof12.db')}")

def setup_server():
    """Setup for server deployment with DynamoDB"""
    load_dotenv('.env.server')
    print("✅ Server environment configured (DynamoDB)")
    print(f"Region: {os.getenv('AWS_REGION')}")
    print(f"Users Table: {os.getenv('USERS_TABLE')}")
    print(f"Companies Table: {os.getenv('COMPANIES_TABLE')}")
    
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
    elif env == "server":
        setup_server()
    else:
        print("Usage: python setup_environment.py [local|server]")