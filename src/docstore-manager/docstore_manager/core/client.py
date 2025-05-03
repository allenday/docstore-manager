"""Base class definition for document store clients."""

import abc
from typing import Any, Dict, List, Optional

class DocumentStoreClient(abc.ABC):
    """Abstract base class for document store client implementations."""

    @abc.abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """Initialize the client with configuration."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def client(self) -> Any:
        """Provides access to the underlying native client instance."""
        raise NotImplementedError

    @abc.abstractmethod
    def list_collections(self) -> List[str]:
        """List all collections/cores in the document store."""
        raise NotImplementedError

    @abc.abstractmethod
    def is_healthy(self) -> bool:
        """Check if the connection to the document store is healthy."""
        raise NotImplementedError

    # --- Add other common abstract methods needed by commands ---
    # Examples (adapt signatures as needed):
    # 
    # @abc.abstractmethod
    # def create_collection(self, name: str, **kwargs) -> None:
    #     raise NotImplementedError
    # 
    # @abc.abstractmethod
    # def delete_collection(self, name: str) -> None:
    #     raise NotImplementedError
    # 
    # @abc.abstractmethod
    # def collection_info(self, name: str) -> Dict[str, Any]:
    #     raise NotImplementedError
    # 
    # @abc.abstractmethod
    # def add_documents(self, collection_name: str, documents: List[Dict[str, Any]], **kwargs) -> None:
    #     raise NotImplementedError
    # 
    # @abc.abstractmethod
    # def delete_documents(self, collection_name: str, ids: Optional[List[str]] = None, query: Optional[str] = None, **kwargs) -> None:
    #     raise NotImplementedError
    # 
    # @abc.abstractmethod
    # def get_documents(self, collection_name: str, ids: List[str], **kwargs) -> List[Dict[str, Any]]:
    #     raise NotImplementedError
    # 
    # @abc.abstractmethod
    # def search_documents(self, collection_name: str, query: Any, limit: int, **kwargs) -> List[Dict[str, Any]]:
    #     raise NotImplementedError
    #
    # @abc.abstractmethod
    # def count_documents(self, collection_name: str, query: Optional[Any] = None) -> int:
    #     raise NotImplementedError 