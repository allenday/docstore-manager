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
1. Analyze the _clean_dict_recursive method in QdrantFormatter class
   - Identify the conditions under which it returns a string instead of a dictionary
   - Understand how the method handles non-serializable types

2. Modify the _clean_dict_recursive method to ensure it always returns a dictionary
   - Update the handling of non-serializable types to maintain dictionary structure
   - Ensure that when converting complex objects to strings, they are properly wrapped in a dictionary

3. Update the format_collection_info method to handle edge cases
   - Strengthen the check for whether cleaned_info is a dictionary
   - Ensure proper fallback behavior when cleaned_info is not a dictionary

4. Add appropriate logging
   - Add debug logging to track the type of cleaned_info
   - Add warning logging when non-dictionary values are encountered

5. Run the failing tests to verify the fix
   - Run tests/qdrant/test_format.py::test_format_collection_info
   - Run tests/qdrant/test_format.py::test_format_collection_info_minimal

## Dependencies
- Requires: None
- Blocks: None

## Expected Output
1. The _clean_dict_recursive method should be updated to ensure it always returns a dictionary when processing collection information.
2. The format_collection_info method should handle all edge cases properly.
3. The tests tests/qdrant/test_format.py::test_format_collection_info and tests/qdrant/test_format.py::test_format_collection_info_minimal should pass.
4. No regressions in other tests that use the QdrantFormatter class.
