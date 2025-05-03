# Implementation Plan: Test Fixes

## Scope
This implementation plan addresses the failing tests and errors in the docstore-manager project. The plan focuses on fixing four specific test failures and sixteen errors identified during test execution. These issues are primarily related to validation errors in the CollectionConfig class, formatting issues in the QdrantFormatter class, and CLI testing context problems. Resolving these issues is a critical step toward the 0.1.0 release to PyPI, as it ensures the core functionality works correctly and can be reliably tested.

## Design Decisions
- **Fix vs. Modify Tests**: In cases where tests are failing due to mismatches between test expectations and actual implementation, we will prioritize fixing the implementation to match the tests rather than modifying the tests to match the implementation. This approach ensures that the tests continue to serve their purpose of validating correct behavior.
- **CollectionConfig Structure**: The CollectionConfig validation errors indicate a mismatch between the expected structure and the provided structure. We will update the CollectionConfig class to properly handle VectorParams objects and include required fields (hnsw_config, optimizer_config).
- **CLI Testing Approach**: For CLI testing, we will consistently use Click's CliRunner instead of calling callback functions directly. This ensures proper setup of the Click context and more reliable testing.
- **Parameter Consistency**: We will ensure consistent parameter handling across functions, particularly for the `with_vectors` parameter in the get_documents function, to maintain expected behavior.

## Algorithms
- **Collection Info Formatting**: The formatting algorithm in QdrantFormatter needs to be updated to handle string inputs correctly, ensuring they are properly converted to dictionaries before merging.
  - Complexity: O(1) - Simple type checking and conversion
- **Parameter Validation**: The parameter validation in get_documents function needs to ensure consistent parameter passing to both client.retrieve and formatter.format_documents methods.
  - Complexity: O(1) - Simple parameter passing
- **CollectionConfig Validation**: The CollectionConfig class needs to be updated to properly validate and handle its required fields.
  - Complexity: O(1) - Validation logic

## Data Flow
```
Test Execution
    │
    ├─── Collection Info Formatting Test
    │       │
    │       ├─── QdrantFormatter.format_collection_info()
    │       │       │
    │       │       └─── _clean_dict_recursive() ──> Returns string instead of dict
    │       │
    │       └─── TypeError: 'str' object is not a mapping
    │
    ├─── CLI Testing
    │       │
    │       ├─── Direct callback invocation ──> No Click context
    │       │
    │       └─── RuntimeError: There is no active click context
    │
    ├─── get_documents Test
    │       │
    │       ├─── get_documents() ──> with_vectors=True
    │       │       │
    │       │       └─── client.retrieve() ──> with_vectors=True
    │       │
    │       └─── AssertionError: Expected with_vectors=False
    │
    └─── CollectionConfig Tests
            │
            ├─── mock_client_fixture() ──> Creates VectorParams
            │       │
            │       └─── CollectionConfig(params=valid_vector_params)
            │
            └─── ValidationError: 3 validation errors for CollectionConfig
```

## Tasks
- [Strategy_fix_collection_info_formatting](../tasks/Strategy_fix_collection_info_formatting.md): Fix the TypeError in format_collection_info method of QdrantFormatter class by ensuring _clean_dict_recursive always returns a dictionary.
- [Strategy_fix_cli_testing_context](../tasks/Strategy_fix_cli_testing_context.md): Resolve the RuntimeError in CLI tests by using Click's CliRunner for all CLI tests.
- [Strategy_fix_parameter_validation](../tasks/Strategy_fix_parameter_validation.md): Update the get_documents function to use with_vectors=False when calling client.retrieve method, or update the test to expect with_vectors=True.
- [Strategy_fix_collectionconfig_validation](../tasks/Strategy_fix_collectionconfig_validation.md): Update the CollectionConfig class to properly handle VectorParams objects and include required fields (hnsw_config, optimizer_config).
