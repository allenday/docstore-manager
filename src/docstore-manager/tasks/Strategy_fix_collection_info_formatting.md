# Task: Fix Collection Info Formatting
**Parent:** `implementation_plan_test_fixes.md`
**Children:** None

## Objective
Fix the TypeError in the format_collection_info method of QdrantFormatter class by ensuring _clean_dict_recursive always returns a dictionary when handling collection information.

## Context
The QdrantFormatter class is responsible for formatting Qdrant responses into user-friendly output. The format_collection_info method is failing with a TypeError: 'str' object is not a mapping when trying to unpack a string using the ** operator:

```python
data = {"name": collection_name, **cleaned_info}
```

The issue occurs because the _clean_dict_recursive method sometimes returns a string instead of a dictionary when it encounters non-serializable types. While there is a check for this case, the current implementation still has a bug that needs to be fixed.

The failing tests are:
- tests/qdrant/test_format.py::test_format_collection_info
- tests/qdrant/test_format.py::test_format_collection_info_minimal

## Steps
1. [DONE] Analyze the _clean_dict_recursive method in QdrantFormatter class
   - Identified that it returns a string instead of a dictionary in the else branch when handling non-serializable types
   - The method attempts to JSON serialize unknown types, and if that fails, it returns a string representation

2. [DONE] Modify the _clean_dict_recursive method to ensure it always returns a dictionary
   - Updated the handling of non-serializable types to wrap string representations in a dictionary
   - Changed the code to return {"value": str(data), "original_type": str(type(data).__name__)} instead of just str(data)

3. [DONE] Update the format_collection_info method to handle edge cases
   - The existing check for whether cleaned_info is a dictionary was already adequate
   - The fallback behavior when cleaned_info is not a dictionary was already properly implemented

4. [DONE] Add appropriate logging
   - The existing warning logging when non-dictionary values are encountered was already in place
   - Updated the warning message to be more descriptive: "Converting non-serializable type {type(data)} to dictionary during formatting."

5. [DONE] Run the failing tests to verify the fix
   - Ran tests/qdrant/test_format.py::test_format_collection_info - PASSED
   - Ran tests/qdrant/test_format.py::test_format_collection_info_minimal - PASSED
   - Ran all tests in tests/qdrant/test_format.py to ensure no regressions - ALL PASSED

## Dependencies
- Requires: None
- Blocks: None

## Expected Output
1. The _clean_dict_recursive method should be updated to ensure it always returns a dictionary when processing collection information.
2. The format_collection_info method should handle all edge cases properly.
3. The tests tests/qdrant/test_format.py::test_format_collection_info and tests/qdrant/test_format.py::test_format_collection_info_minimal should pass.
4. No regressions in other tests that use the QdrantFormatter class.
