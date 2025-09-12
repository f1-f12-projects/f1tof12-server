#!/usr/bin/env python3
import os
from dotenv import load_dotenv

def load_environment():
    """Load environment-specific configuration"""
    env = os.getenv('ENVIRONMENT', 'dev')
    
    # Load environment-specific config
    env_file = f'.env.{env}'
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"Loaded {env} environment configuration")
    else:
        print(f"Warning: {env_file} not found, using default configuration")

if __name__ == "__main__":
    load_environment()