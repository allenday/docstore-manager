# Test Failures Report

## Overview
This report documents the failing tests identified in the docstore-manager project on 2025-05-03. The tests were run using pytest with the project-specific virtual environment (src/docstore-manager/.venv).

## Summary
- **Total Tests**: 378
- **Passed**: 352
- **Failed**: 4
- **Errors**: 16
- **Skipped**: 6

## Failed Tests

### 1. tests/qdrant/test_format.py::test_format_collection_info
**Error**: `TypeError: 'str' object is not a mapping`

This error occurs in the `format_collection_info` method of the `QdrantFormatter` class. The error happens when trying to merge a string with a dictionary using the `**` operator:
```python
data = {"name": collection_name, **cleaned_info}
```
The issue is that `cleaned_info` is a string, not a dictionary as expected.

### 2. tests/qdrant/test_format.py::test_format_collection_info_minimal
**Error**: `TypeError: 'str' object is not a mapping`

This is the same issue as the previous test, occurring in the same method but with a different test case using minimal collection information.

### 3. tests/qdrant/test_qdrant_cli.py::test_cli_client_load_failure
**Error**: `RuntimeError: There is no active click context.`

This error occurs when trying to access the click context in a test environment. The test is attempting to simulate a CLI command failure, but the click context is not properly set up in the test environment.

### 4. tests/qdrant/test_qdrant_command.py::test_get_documents_success
**Error**: `AssertionError: expected call not found.`

This test is checking that the `retrieve` method of the `QdrantClient` is called with specific parameters, but the actual call used different parameters:
- Expected: `retrieve(collection_name='test_get_docs', ids=['id_a', 'id_b'], with_payload=True, with_vectors=False)`
- Actual: `retrieve(collection_name='test_get_docs', ids=['id_a', 'id_b'], with_payload=True, with_vectors=True)`

The difference is in the `with_vectors` parameter, which is `True` in the actual call but expected to be `False`.

## Errors

There are 16 errors in tests/qdrant/test_qdrant_cli.py, all related to the same validation issue with `CollectionConfig`:

```
pydantic_core._pydantic_core.ValidationError: 3 validation errors for CollectionConfig
params
  Input should be a valid dictionary or instance of CollectionParams [type=model_type, input_value=VectorParams(size=4, dist...multivector_config=None), input_type=VectorParams]
    For further information visit https://errors.pydantic.dev/2.11/v/model_type
hnsw_config
  Field required [type=missing, input_value={'params': VectorParams(s...ultivector_config=None)}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.11/v/missing
optimizer_config
  Field required [type=missing, input_value={'params': VectorParams(s...ultivector_config=None)}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.11/v/missing
```

These errors occur in the test fixture `mock_client_fixture` when trying to create a `CollectionConfig` object with a `VectorParams` object. The issue is that the `CollectionConfig` class expects:
1. A dictionary or `CollectionParams` instance for the `params` field, not a `VectorParams` object
2. The `hnsw_config` field is required but missing
3. The `optimizer_config` field is required but missing

## Potential Fixes

### For the format tests:
The `_clean_dict_recursive` method in `QdrantFormatter` might be returning a string instead of a dictionary. The method should be modified to ensure it always returns a dictionary.

### For the CLI test:
The test needs to properly set up a click context before testing CLI commands. This can be done using the `click.Context` class or by using the `CliRunner` from click's testing utilities.

### For the get_documents test:
The `get_documents` function in `cmd_get.py` should be updated to use `with_vectors=False` when calling the `retrieve` method, or the test should be updated to expect `with_vectors=True`.

### For the CollectionConfig validation errors:
The test fixture needs to be updated to create a valid `CollectionConfig` object with all required fields. This might involve:
1. Using a `CollectionParams` object instead of `VectorParams` for the `params` field
2. Adding the required `hnsw_config` and `optimizer_config` fields

## Conclusion
The failing tests indicate issues with the formatting of collection information, CLI command testing, parameter validation in the get_documents function, and validation of the CollectionConfig object. These issues should be addressed during the Strategy or Execution phase of the project.
