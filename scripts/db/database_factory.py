import os
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class DatabaseInterface(ABC):
    @abstractmethod
    def create_user(self, username: str, hashed_password: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def create_company(self, name: str, spoc: str, email_id: str, status: str = "active") -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_company_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def list_companies(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def update_company(self, company_id: int, update_data: Dict[str, Any]) -> bool:
        pass

def get_database() -> DatabaseInterface:
    """Factory function to return appropriate database implementation"""
    from scripts.db.config import USE_DYNAMODB
    if USE_DYNAMODB:
        from scripts.db.dynamodb_adapter import DynamoDBAdapter
        return DynamoDBAdapter()
    else:
        from scripts.db.sqlite_adapter import SQLiteAdapter
        return SQLiteAdapter()