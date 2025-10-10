import boto3
from botocore.exceptions import ClientError
from scripts.db.config import AWS_REGION, USERS_TABLE, COMPANIES_TABLE, SPOCS_TABLE, INVOICES_TABLE, REQUIREMENTS_TABLE, REQUIREMENT_STATUSES_TABLE, PROFILE_STATUSES_TABLE, COUNTERS_TABLE, PROFILES_TABLE

def create_dynamodb_tables():
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    
    tables = [
        {
            'name': USERS_TABLE,
            'key': 'username',
            'type': 'S'
        },
        {
            'name': COMPANIES_TABLE,
            'key': 'id',
            'type': 'N'
        },
        {
            'name': SPOCS_TABLE,
            'key': 'id',
            'type': 'N'
        },
        {
            'name': INVOICES_TABLE,
            'key': 'id',
            'type': 'N'
        },
        {
            'name': REQUIREMENTS_TABLE,
            'key': 'requirement_id',
            'type': 'N'
        },
        {
            'name': PROFILES_TABLE,
            'key': 'profile_id',
            'type': 'N'
        },
        {
            'name': REQUIREMENT_STATUSES_TABLE,
            'key': 'id',
            'type': 'N'
        },
        {
            'name': PROFILE_STATUSES_TABLE,
            'key': 'id',
            'type': 'N'
        },
        {
            'name': COUNTERS_TABLE,
            'key': 'table_name',
            'type': 'S'
        }
    ]
    
    for table_config in tables:
        try:
            table = dynamodb.create_table(
                TableName=table_config['name'],
                KeySchema=[{'AttributeName': table_config['key'], 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': table_config['key'], 'AttributeType': table_config['type']}],
                BillingMode='PAY_PER_REQUEST'
            )
            print(f"Created table: {table.table_name}")
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == 'ResourceInUseException':
                print(f"Table {table_config['name']} already exists")
            else:
                raise

if __name__ == "__main__":
    create_dynamodb_tables()