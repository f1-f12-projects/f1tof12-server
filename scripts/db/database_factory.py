

def get_database():
    """Factory function to return appropriate database implementation"""
    from scripts.db.config import USE_DYNAMODB
    if USE_DYNAMODB:
        from scripts.db.dynamodb_adapter import DynamoDBAdapter
        return DynamoDBAdapter()
    else:
        from scripts.db.sqlite_adapter import SQLiteAdapter
        return SQLiteAdapter()