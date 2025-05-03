# Extension Points

This page describes the extension points available in docstore-manager for adding support for new document stores or enhancing existing functionality.

## Adding Support for a New Document Store

docstore-manager is designed to be extensible, allowing you to add support for additional document store databases beyond the built-in Qdrant and Solr support.

### Step 1: Create a New Module

Create a new module in the `docstore_manager` package:

```
docstore_manager/
├── core/
├── qdrant/
├── solr/
└── your_new_store/  # New module
    ├── __init__.py
    ├── cli.py
    ├── client.py
    ├── command.py
    ├── config.py
    ├── format.py
    └── utils.py
```

### Step 2: Implement the Required Interfaces

Implement the following interfaces from the core module:

1. **ClientInterface** (`client_interface.py`):
   - Implement a client class that inherits from `ClientInterface`
   - Implement all required methods for connecting to and interacting with your document store

2. **CommandInterface** (`command_interface.py`):
   - Implement a command class that inherits from `CommandInterface`
   - Implement all required methods for executing commands against your document store

3. **Formatter** (optional):
   - Implement a formatter class for formatting the output of your document store's responses

### Step 3: Create a CLI Module

Create a CLI module that exposes your document store's functionality through the command line:

```python
import click
from docstore_manager.core.cli import common_options

@click.group()
def your_store():
    """Commands for managing Your Store."""
    pass

@your_store.command()
@common_options
def list_collections(config, output_format):
    """List all collections in Your Store."""
    # Implementation
    pass

# Add more commands...
```

### Step 4: Register Your CLI Commands

Register your CLI commands in the main CLI module (`docstore_manager/cli.py`):

```python
from docstore_manager.your_new_store.cli import your_store

cli.add_command(your_store)
```

## Enhancing Existing Document Stores

You can enhance the existing Qdrant or Solr support by:

1. **Adding New Commands**:
   - Add new command methods to the respective command classes
   - Add new CLI commands to expose the functionality

2. **Extending Formatters**:
   - Enhance the formatting capabilities for specific document store responses

3. **Adding Utilities**:
   - Create utility functions for common operations

## Core Extension Points

The core module provides several extension points:

### Configuration System

The configuration system can be extended to support additional configuration options:

```python
from docstore_manager.core.config import ConfigBase

class YourStoreConfig(ConfigBase):
    """Configuration for Your Store."""

    def __init__(self, host, port, **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self.port = port
```

### Command System

The command system can be extended with new base command types:

```python
from docstore_manager.core.command import CommandBase

class YourCommandType(CommandBase):
    """Base class for your custom command type."""

    def execute(self):
        """Execute the command."""
        raise NotImplementedError
```

### Formatting System

The formatting system can be extended with new formatters:

```python
from docstore_manager.core.format import FormatterBase

class YourFormatter(FormatterBase):
    """Formatter for your custom output format."""

    def format_output(self, data):
        """Format the output data."""
        raise NotImplementedError
```

## Examples

For examples of how to implement these extension points, see the existing implementations:

- Qdrant implementation: `docstore_manager/qdrant/`
- Solr implementation: `docstore_manager/solr/`

These provide good reference implementations that you can use as a starting point for your own extensions.
