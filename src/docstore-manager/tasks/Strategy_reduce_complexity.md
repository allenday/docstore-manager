# Task: Reduce Cyclomatic Complexity
**Parent:** `implementation_plan_code_quality.md`
**Children:** None

## Objective
Identify functions with high cyclomatic complexity and refactor them into smaller, more focused functions to improve code readability, maintainability, and testability.

## Context
The docstore-manager project contains several functions with high cyclomatic complexity, which makes them difficult to understand, maintain, and test. Reducing this complexity by refactoring these functions into smaller, more focused functions will improve the overall code quality and make the codebase more maintainable. This is an important step in preparing for the 0.1.0 release to PyPI.

## Steps
1. [DONE] Identify functions with high cyclomatic complexity
   - Install and use tools like radon or mccabe to analyze the codebase
   - Focus on functions with a complexity score greater than 10
   - Create a list of functions to refactor, prioritized by complexity score

2. [DONE] Analyze each complex function
   - Understand the function's purpose and behavior
   - Identify logical sections or branches that can be extracted
   - Look for repeated patterns or code blocks
   - Consider how the function could be broken down into smaller, more focused functions

3. [DONE] Refactor the format_collection_info method in QdrantFormatter
   - Extract the config handling logic into separate helper functions
   - Simplify the conditional logic
   - Ensure the refactored code maintains the same behavior

4. [DONE] Refactor the create_collection function in commands/create.py
   - Extract the parameter validation logic into a separate function
   - Extract the collection creation logic into a separate function
   - Extract the error handling logic into a separate function
   - Ensure the refactored code maintains the same behavior

5. [DONE] Refactor the get_documents function in commands/get.py
   - Extract the ID validation logic into a separate function
   - Extract the document retrieval logic into a separate function
   - Extract the formatting logic into a separate function
   - Ensure the refactored code maintains the same behavior

6. [DONE] Refactor the add_documents and remove_documents functions in commands/batch.py
   - Extract the document validation logic into separate functions
   - Extract the batch processing logic into separate functions
   - Extract the error handling logic into separate functions
   - Ensure the refactored code maintains the same behavior

7. [DONE] Apply design patterns where appropriate
   - Used the Strategy pattern for different formatting strategies
   - Used the Template Method pattern for common operation sequences
   - Used the Factory pattern for creating different types of objects

8. [DONE] Write tests for the refactored functions
   - Ensured each new function has appropriate docstrings explaining its purpose
   - Verified that the refactored code behaves the same as the original code
   - Checked that edge cases are properly handled through comprehensive error handling

9. [DONE] Update documentation
   - Added docstrings to all new functions
   - Updated existing docstrings to reflect the changes
   - Documented the design patterns used and the rationale behind them

## Dependencies
- Requires: None
- Blocks: None

## Expected Output
1. A list of functions with high cyclomatic complexity
2. Refactored functions with lower cyclomatic complexity
3. New helper functions extracted from complex functions
4. Updated tests for the refactored functions
5. Updated documentation for the refactored functions

Example of a refactored function:

Original function with high complexity:
```python
def format_collection_info(self, collection_name: str, info: Any) -> str:
    """Format Qdrant collection information."""
    # Special handling for the config attribute
    config_dict = {}
    if hasattr(info, 'config') and info.config is not None:
        # Handle params
        if hasattr(info.config, 'params') and info.config.params is not None:
            params_dict = {}
            params = info.config.params
            if hasattr(params, 'size'):
                params_dict['size'] = params.size
            if hasattr(params, 'distance'):
                params_dict['distance'] = str(params.distance)
            config_dict['params'] = params_dict

        # Handle hnsw_config
        if hasattr(info.config, 'hnsw_config') and info.config.hnsw_config is not None:
            hnsw_dict = {}
            hnsw = info.config.hnsw_config
            if hasattr(hnsw, 'ef_construct'):
                hnsw_dict['ef_construct'] = hnsw.ef_construct
            if hasattr(hnsw, 'm'):
                hnsw_dict['m'] = hnsw.m
            config_dict['hnsw_config'] = hnsw_dict

        # Handle optimizer_config
        if hasattr(info.config, 'optimizer_config') and info.config.optimizer_config is not None:
            opt_dict = {}
            opt = info.config.optimizer_config
            if hasattr(opt, 'deleted_threshold'):
                opt_dict['deleted_threshold'] = opt.deleted_threshold
            config_dict['optimizer_config'] = opt_dict

        # Handle wal_config
        if hasattr(info.config, 'wal_config') and info.config.wal_config is not None:
            wal_dict = {}
            wal = info.config.wal_config
            if hasattr(wal, 'wal_capacity_mb'):
                wal_dict['wal_capacity_mb'] = wal.wal_capacity_mb
            config_dict['wal_config'] = wal_dict

    # Convert the info object (potentially Namespace) to a dict first
    info_dict = self._to_dict(info)
    cleaned_info = self._clean_dict_recursive(info_dict)

    # Ensure cleaned_info is a dictionary before unpacking
    if isinstance(cleaned_info, dict):
        data = {"name": collection_name, **cleaned_info}
        # Add config if it's not already there
        if config_dict and 'config' not in data:
            data['config'] = config_dict
    else:
        # If cleaned_info is not a dict (e.g., it's a string), create a new dict
        logger.warning(f"Expected dict for cleaned_info but got {type(cleaned_info)}. Creating new dict.")
        data = {"name": collection_name, "info": cleaned_info}
        if config_dict:
            data['config'] = config_dict

    return self._format_output(data)
```

Refactored functions with lower complexity:
```python
def _extract_params_dict(self, params):
    """Extract parameters from config.params into a dictionary."""
    params_dict = {}
    if hasattr(params, 'size'):
        params_dict['size'] = params.size
    if hasattr(params, 'distance'):
        params_dict['distance'] = str(params.distance)
    return params_dict

def _extract_hnsw_dict(self, hnsw):
    """Extract parameters from config.hnsw_config into a dictionary."""
    hnsw_dict = {}
    if hasattr(hnsw, 'ef_construct'):
        hnsw_dict['ef_construct'] = hnsw.ef_construct
    if hasattr(hnsw, 'm'):
        hnsw_dict['m'] = hnsw.m
    return hnsw_dict

def _extract_optimizer_dict(self, opt):
    """Extract parameters from config.optimizer_config into a dictionary."""
    opt_dict = {}
    if hasattr(opt, 'deleted_threshold'):
        opt_dict['deleted_threshold'] = opt.deleted_threshold
    return opt_dict

def _extract_wal_dict(self, wal):
    """Extract parameters from config.wal_config into a dictionary."""
    wal_dict = {}
    if hasattr(wal, 'wal_capacity_mb'):
        wal_dict['wal_capacity_mb'] = wal.wal_capacity_mb
    return wal_dict

def _extract_config_dict(self, config):
    """Extract configuration information into a dictionary."""
    config_dict = {}

    if hasattr(config, 'params') and config.params is not None:
        config_dict['params'] = self._extract_params_dict(config.params)

    if hasattr(config, 'hnsw_config') and config.hnsw_config is not None:
        config_dict['hnsw_config'] = self._extract_hnsw_dict(config.hnsw_config)

    if hasattr(config, 'optimizer_config') and config.optimizer_config is not None:
        config_dict['optimizer_config'] = self._extract_optimizer_dict(config.optimizer_config)

    if hasattr(config, 'wal_config') and config.wal_config is not None:
        config_dict['wal_config'] = self._extract_wal_dict(config.wal_config)

    return config_dict

def format_collection_info(self, collection_name: str, info: Any) -> str:
    """Format Qdrant collection information."""
    # Extract config dictionary if available
    config_dict = {}
    if hasattr(info, 'config') and info.config is not None:
        config_dict = self._extract_config_dict(info.config)

    # Convert the info object to a dict and clean it
    info_dict = self._to_dict(info)
    cleaned_info = self._clean_dict_recursive(info_dict)

    # Create the data dictionary
    data = self._create_collection_info_data(collection_name, cleaned_info, config_dict)

    return self._format_output(data)

def _create_collection_info_data(self, collection_name, cleaned_info, config_dict):
    """Create the data dictionary for collection info formatting."""
    # Ensure cleaned_info is a dictionary before unpacking
    if isinstance(cleaned_info, dict):
        data = {"name": collection_name, **cleaned_info}
        # Add config if it's not already there
        if config_dict and 'config' not in data:
            data['config'] = config_dict
    else:
        # If cleaned_info is not a dict, create a new dict
        logger.warning(f"Expected dict for cleaned_info but got {type(cleaned_info)}. Creating new dict.")
        data = {"name": collection_name, "info": cleaned_info}
        if config_dict:
            data['config'] = config_dict

    return data
