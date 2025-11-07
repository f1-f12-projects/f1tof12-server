import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# ruff: noqa: E402
import boto3
from scripts.db.config import (
    AWS_REGION, COMPANIES_TABLE, SPOCS_TABLE, INVOICES_TABLE, 
    REQUIREMENTS_TABLE, COUNTERS_TABLE, PROFILES_TABLE, PROCESS_PROFILES_TABLE,
    LEAVES_TABLE, LEAVE_BALANCES_TABLE, HOLIDAYS_TABLE, USER_HOLIDAY_SELECTIONS_TABLE
)

def clear_table(dynamodb, table_name, key_name):
    """Clear all items from a DynamoDB table"""
    table = dynamodb.Table(table_name)
    
    try:
        response = table.scan(ProjectionExpression=key_name)
        
        with table.batch_writer() as batch:
            for item in response['Items']:
                batch.delete_item(Key={key_name: item[key_name]})
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ProjectionExpression=key_name,
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            with table.batch_writer() as batch:
                for item in response['Items']:
                    batch.delete_item(Key={key_name: item[key_name]})
        
        print(f"✓ Cleared {table_name}")
    except Exception as e:
        print(f"✗ Failed to clear {table_name}: {str(e)}")

def main():
    # Table to counter mapping
    table_counter_map = {
        COMPANIES_TABLE: 'companies',
        SPOCS_TABLE: 'spocs', 
        INVOICES_TABLE: 'invoices',
        REQUIREMENTS_TABLE: 'requirements',
        PROFILES_TABLE: 'profiles',
        PROCESS_PROFILES_TABLE: 'process_profiles',
        LEAVES_TABLE: 'leaves',
        LEAVE_BALANCES_TABLE: 'leave_balances',
        HOLIDAYS_TABLE: 'holidays',
        USER_HOLIDAY_SELECTIONS_TABLE: 'user_holiday_selections'
    }
    
    tables = [
        (COMPANIES_TABLE, 'id'),
        (SPOCS_TABLE, 'id'),
        (INVOICES_TABLE, 'id'),
        (REQUIREMENTS_TABLE, 'requirement_id'),
        (PROFILES_TABLE, 'id'),
        (PROCESS_PROFILES_TABLE, 'id'),
        (LEAVES_TABLE, 'id'),
        (LEAVE_BALANCES_TABLE, 'id'),
        (HOLIDAYS_TABLE, 'id'),
        (USER_HOLIDAY_SELECTIONS_TABLE, 'id'),
    ]
    
    print("Available tables:")
    for i, (table_name, _) in enumerate(tables, 1):
        print(f"{i}. {table_name}")
    
    choice = input("\nEnter table numbers to delete (comma-separated) or 'all': ")
    
    if choice.lower() == 'all':
        selected_tables = tables
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected_tables = [tables[i] for i in indices if 0 <= i < len(tables)]
        except (ValueError, IndexError):
            print("Invalid selection")
            return
    
    if not selected_tables:
        print("No tables selected")
        return
    
    print(f"\nWill delete {len(selected_tables)} table(s). Type 'DELETE' to confirm: ", end='')
    if input() != 'DELETE':
        print("Operation cancelled")
        return
    
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    
    for table_name, key_name in selected_tables:
        clear_table(dynamodb, table_name, key_name)
        
        # Reset specific counter
        counter_name = table_counter_map[table_name]
        try:
            table = dynamodb.Table(COUNTERS_TABLE)
            table.put_item(Item={'table_name': counter_name, 'next_id': 1})
            print(f"✓ Reset {counter_name} counter")
        except Exception as e:
            print(f"✗ Failed to reset {counter_name} counter: {str(e)}")
    
    print("\nSelected tables cleared and counters reset!")

if __name__ == "__main__":
    main()