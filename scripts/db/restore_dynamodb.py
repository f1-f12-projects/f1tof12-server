import boto3
import json
import os
import sys
from decimal import Decimal

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from scripts.db.config import AWS_REGION

def convert_floats_to_decimal(obj):
    """Convert float values to Decimal for DynamoDB compatibility"""
    if isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj

def restore_table(dynamodb, table_name, backup_file):
    """Restore a single DynamoDB table from backup"""
    if not os.path.exists(backup_file):
        print(f"✗ Backup file not found: {backup_file}")
        return 0
    
    table = dynamodb.Table(table_name)
    
    try:
        with open(backup_file, 'r') as f:
            items = json.load(f)
        
        # Convert floats to Decimal and batch write
        for item in items:
            converted_item = convert_floats_to_decimal(item)
            table.put_item(Item=converted_item)
        
        print(f"✓ Restored {table_name}: {len(items)} items")
        return len(items)
    
    except Exception as e:
        print(f"✗ Failed to restore {table_name}: {str(e)}")
        return 0

def main():
    if len(sys.argv) != 2:
        print("Usage: python restore_dynamodb.py <backup_directory>")
        sys.exit(1)
    
    backup_dir = sys.argv[1]
    
    if not os.path.exists(backup_dir):
        print(f"Backup directory not found: {backup_dir}")
        sys.exit(1)
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    
    print(f"Starting DynamoDB restore from: {backup_dir}")
    total_items = 0
    
    # Restore all JSON files in backup directory
    for filename in os.listdir(backup_dir):
        if filename.endswith('.json'):
            table_name = filename[:-5]  # Remove .json extension
            backup_file = os.path.join(backup_dir, filename)
            items_count = restore_table(dynamodb, table_name, backup_file)
            total_items += items_count
    
    print(f"\nRestore completed: {total_items} total items restored")

if __name__ == "__main__":
    main()