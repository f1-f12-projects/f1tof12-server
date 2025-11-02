import boto3
import json
import os
from datetime import datetime
from decimal import Decimal
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from scripts.db.config import (
    AWS_REGION, COMPANIES_TABLE, SPOCS_TABLE, INVOICES_TABLE, 
    REQUIREMENTS_TABLE, REQUIREMENT_STATUSES_TABLE, PROFILE_STATUSES_TABLE,
    COUNTERS_TABLE, PROFILES_TABLE, PROCESS_PROFILES_TABLE
)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def backup_table(dynamodb, table_name, backup_dir):
    """Backup a single DynamoDB table"""
    table = dynamodb.Table(table_name)
    
    try:
        response = table.scan()
        items = response['Items']
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])
        
        # Save to JSON file
        backup_file = os.path.join(backup_dir, f"{table_name}.json")
        with open(backup_file, 'w') as f:
            json.dump(items, f, cls=DecimalEncoder, indent=2)
        
        print(f"✓ Backed up {table_name}: {len(items)} items")
        return len(items)
    
    except Exception as e:
        print(f"✗ Failed to backup {table_name}: {str(e)}")
        return 0

def main():
    # Create backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"dynamodb_backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    
    tables = [
        COMPANIES_TABLE,
        SPOCS_TABLE,
        INVOICES_TABLE,
        REQUIREMENTS_TABLE,
        REQUIREMENT_STATUSES_TABLE,
        PROFILE_STATUSES_TABLE,
        COUNTERS_TABLE,
        PROFILES_TABLE,
        PROCESS_PROFILES_TABLE
    ]
    
    print(f"Starting DynamoDB backup to: {backup_dir}")
    total_items = 0
    
    for table_name in tables:
        items_count = backup_table(dynamodb, table_name, backup_dir)
        total_items += items_count
    
    print(f"\nBackup completed: {total_items} total items backed up to {backup_dir}")

if __name__ == "__main__":
    main()