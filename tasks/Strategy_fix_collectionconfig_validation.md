# Task: Fix CollectionConfig Validation Errors
**Parent:** `implementation_plan_test_fixes.md`
**Children:** None

## Objective
Update the CollectionConfig creation in the mock_client_fixture function to properly handle VectorParams objects and include required fields (hnsw_config, optimizer_config).

## Context
There are 16 errors in tests/qdrant/test_qdrant_cli.py, all related to the same validation issue with CollectionConfig. The errors occur in the test fixture mock_client_fixture when trying to create a CollectionConfig object with a VectorParams object.

The issue is that the CollectionConfig class expects:
1. A dictionary or CollectionParams instance for the params field, not a VectorParams object
2. The hnsw_config field is required but missing
3. The optimizer_config field is required but missing

The failing tests are all in tests/qdrant/test_qdrant_cli.py.

## Steps
1. Analyze the mock_client_fixture function in tests/qdrant/test_qdrant_cli.py
   - Understand how the CollectionConfig object is created
   - Identify the validation errors

2. Update the CollectionConfig creation to include all required fields
   - Create a CollectionParams object instead of using VectorParams directly
   - Add the required hnsw_config field
   - Add the required optimizer_config field

3. Alternatively, if the CollectionConfig class has changed in a newer version of the Qdrant client
   - Check the current version of the Qdrant client being used
   - Check the CollectionConfig class definition in the current version
   - Update the mock_client_fixture function to match the current CollectionConfig requirements

4. Run the failing tests to verify the fix
   - Run tests/qdrant/test_qdrant_cli.py

## Dependencies
- Requires: None
- Blocks: None

## Expected Output
1. The mock_client_fixture function should be updated to create a valid CollectionConfig object.
2. The tests in tests/qdrant/test_qdrant_cli.py should pass without the validation errors.
3. No regressions in other tests that use the mock_client_fixture function.
