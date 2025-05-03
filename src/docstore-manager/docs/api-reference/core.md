# Core API Reference

This section provides detailed API reference for the Core module of docstore-manager.

## Client Interface

::: docstore_manager.core.client_interface
    options:
      show_root_heading: true
      show_source: true

## Command Interface

::: docstore_manager.core.command_interface
    options:
      show_root_heading: true
      show_source: true

## Format Interface

::: docstore_manager.core.format.formatter_interface
    options:
      show_root_heading: true
      show_source: true

::: docstore_manager.core.format.base_formatter
    options:
      show_root_heading: true
      show_source: true

## Utilities

::: docstore_manager.core.utils
    options:
      show_root_heading: true
      show_source: true

## Examples

### Example 1: Creating a Custom Client

```python
from docstore_manager.core.client_interface import ClientInterface

class MyCustomClient(ClientInterface):
    def __init__(self, url, **kwargs):
        self.url = url
        self.kwargs = kwargs
        
    def initialize(self):
        # Custom initialization logic
        print(f"Initializing connection to {self.url}")
        return True
        
    def list_collections(self):
        # Custom implementation
        return ["collection1", "collection2"]
        
    # Implement other required methods...
```

### Example 2: Creating a Custom Command

```python
from docstore_manager.core.command_interface import CommandInterface

class MyCustomCommand(CommandInterface):
    def __init__(self, client):
        self.client = client
        
    def list_collections(self):
        # Custom implementation with additional logic
        collections = self.client.list_collections()
        return {
            "count": len(collections),
            "collections": collections,
            "timestamp": "2025-05-04T00:00:00Z"
        }
        
    # Implement other required methods...
```
