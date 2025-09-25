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
    
    @abstractmethod
    def create_spoc(self, company_id: int, name: str, phone: str, email_id: str, location: str, status: str = "active") -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def list_spocs(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def update_spoc(self, spoc_id: int, update_data: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def list_invoices(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def get_invoice(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def update_invoice(self, invoice_id: int, update_data: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def create_requirement(self, requirement_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def list_requirements(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def get_requirement(self, requirement_id: int) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def update_requirement(self, requirement_id: int, update_data: Dict[str, Any]) -> bool:
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