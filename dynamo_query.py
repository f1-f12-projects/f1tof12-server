#!/usr/bin/env python3
import boto3
import json
import sys
from boto3.dynamodb.conditions import Key, Attr

class DynamoQuery:
    def __init__(self, region='ap-south-1'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.client = boto3.client('dynamodb', region_name=region)
    
    def schema(self, table_name):
        """Show table schema"""
        try:
            table = self.dynamodb.Table(table_name)
            response = self.client.describe_table(TableName=table_name)
            
            print(f"\n📋 Schema for {table_name}:")
            print(f"Status: {response['Table']['TableStatus']}")
            print(f"Items: {response['Table']['ItemCount']}")
            
            print("\n🔑 Key Schema:")
            for key in response['Table']['KeySchema']:
                print(f"  {key['AttributeName']} ({key['KeyType']})")
            
            print("\n📊 Defined Attributes:")
            for attr in response['Table']['AttributeDefinitions']:
                print(f"  {attr['AttributeName']}: {attr['AttributeType']}")
            
            # Get actual fields from sample data
            scan_response = table.scan(Limit=1)
            if scan_response['Items']:
                sample_item = scan_response['Items'][0]
                print("\n📝 All Fields (from sample):")
                for field, value in sample_item.items():
                    field_type = type(value).__name__
                    print(f"  {field}: {field_type}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def fields(self, table_name):
        """Show all fields from actual data"""
        try:
            table = self.dynamodb.Table(table_name)
            response = table.scan(Limit=10)
            
            all_fields = set()
            for item in response['Items']:
                all_fields.update(item.keys())
            
            print(f"\n📝 All Fields in {table_name}:")
            for field in sorted(all_fields):
                print(f"  {field}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def select(self, table_name, fields=None, **kwargs):
        """Select with where clause and specific fields"""
        try:
            table = self.dynamodb.Table(table_name)
            
            # Build filter expression
            filter_expr = None
            for key, value in kwargs.items():
                condition = Attr(key).eq(value)
                filter_expr = condition if filter_expr is None else filter_expr & condition
            
            # Scan with filter and projection
            scan_kwargs = {}
            if filter_expr:
                scan_kwargs['FilterExpression'] = filter_expr
            if fields:
                # Handle reserved keywords with expression attribute names
                reserved_words = {'status', 'name', 'type', 'data', 'timestamp', 'count', 'size'}
                expr_attr_names = {}
                projection_fields = []
                
                for field in fields:
                    if field.lower() in reserved_words:
                        alias = f'#{field}'
                        expr_attr_names[alias] = field
                        projection_fields.append(alias)
                    else:
                        projection_fields.append(field)
                
                scan_kwargs['ProjectionExpression'] = ','.join(projection_fields)
                if expr_attr_names:
                    scan_kwargs['ExpressionAttributeNames'] = expr_attr_names
            
            response = table.scan(**scan_kwargs)
            
            items = response['Items']
            print(f"\n📄 Found {len(items)} items:")
            for item in items:
                print(json.dumps(item, indent=2, default=str))
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def query_pk(self, table_name, pk_name, pk_value):
        """Query by partition key"""
        try:
            table = self.dynamodb.Table(table_name)
            response = table.query(KeyConditionExpression=Key(pk_name).eq(pk_value))
            
            items = response['Items']
            print(f"\n📄 Found {len(items)} items:")
            for item in items:
                print(json.dumps(item, indent=2, default=str))
                
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python dynamo_query.py schema <table_name>")
        print("  python dynamo_query.py select <table_name> [--fields field1,field2] [key=value ...]")
        print("  python dynamo_query.py query <table_name> <pk_name> <pk_value>")
        print("  python dynamo_query.py fields <table_name>")
        return
    
    dq = DynamoQuery()
    command = sys.argv[1]
    table_name = sys.argv[2]
    
    if command == 'schema':
        dq.schema(table_name)
    elif command == 'fields':
        dq.fields(table_name)
    elif command == 'select':
        # Parse --fields and key=value pairs
        filters = {}
        fields = None
        args = sys.argv[3:]
        
        i = 0
        while i < len(args):
            if args[i] == '--fields' and i + 1 < len(args):
                fields = args[i + 1].split(',')
                i += 2
            elif '=' in args[i]:
                key, value = args[i].split('=', 1)
                filters[key] = value
                i += 1
            else:
                i += 1
        
        dq.select(table_name, fields=fields, **filters)
    elif command == 'query':
        if len(sys.argv) < 5:
            print("Usage: python dynamo_query.py query <table_name> <pk_name> <pk_value>")
            return
        pk_name = sys.argv[3]
        pk_value = sys.argv[4]
        dq.query_pk(table_name, pk_name, pk_value)

if __name__ == '__main__':
    main()