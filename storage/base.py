from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseStorage(ABC):
    """
    Abstract base class for storage backends.
    
    Use this as a template for implementing custom storage backends.
    Examples: Google Sheets, MongoDB, PostgreSQL, Redis, etc.
    """
    
    @abstractmethod
    async def save_data(self, destination_id: str, data: Dict[str, Any]) -> str:
        """
        Saves data to the storage backend.
        
        Args:
            destination_id: The ID of the destination (e.g., collection name, sheet ID).
            data: A dictionary containing the data to save.
            
        Returns:
            The ID of the saved record.
        """
        pass
    
    @abstractmethod
    async def get_data(self, destination_id: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves data from the storage backend.
        
        Args:
            destination_id: The ID of the destination.
            record_id: The ID of the record to retrieve.
            
        Returns:
            The data dictionary if found, None otherwise.
        """
        pass
    
    @abstractmethod
    async def update_data(self, destination_id: str, record_id: str, data: Dict[str, Any]) -> bool:
        """
        Updates data in the storage backend.
        
        Args:
            destination_id: The ID of the destination.
            record_id: The ID of the record to update.
            data: The updated data.
            
        Returns:
            True if successful, False otherwise.
        """
        pass
