# Task: Update Version Number
**Parent:** `implementation_plan_release_prep.md`
**Children:** None

## Objective
Update the version number to 0.1.0 in all relevant files to prepare for the initial release of the docstore-manager project to PyPI.

## Context
The docstore-manager project is preparing for its 0.1.0 release to PyPI. The version number needs to be updated in all relevant files to reflect this initial release. Following semantic versioning (SemVer), the version 0.1.0 indicates a pre-1.0 release with some features but not yet stable.

## Steps
1. Identify all files that contain version information
   - Check pyproject.toml
   - Check setup.py (if it exists)
   - Check __init__.py files in all packages
   - Check any other files that might contain version information (e.g., documentation, README)

2. Update version in pyproject.toml
   - Locate the version field in the [project] section
   - Update the version to "0.1.0"
   - Ensure the format follows semantic versioning

3. Update version in setup.py (if it exists)
   - Locate the version parameter in the setup() function
   - Update the version to "0.1.0"
   - Ensure the format follows semantic versioning

4. Update version in __init__.py files
   - Locate the __version__ variable in each package's __init__.py file
   - Update the version to "0.1.0"
   - Ensure the format follows semantic versioning

5. Update version in documentation
   - Check README.md for any version references
   - Check any other documentation files for version references
   - Update all references to the version to "0.1.0"

6. Ensure consistency across all files
   - Verify that all version references have been updated to "0.1.0"
   - Ensure that the version format is consistent across all files

7. Update CHANGELOG.md
   - Add an entry for the 0.1.0 release
   - List all major features and changes included in this release
   - Include the release date

8. Commit the changes
   - Create a commit with a message like "Update version to 0.1.0 for initial release"
   - Push the changes to the repository

## Dependencies
- Requires: None
- Blocks: None

## Expected Output
1. All relevant files updated with the version number 0.1.0
2. Consistent version format across all files
3. Updated CHANGELOG.md with an entry for the 0.1.0 release
4. Commit with all version updates

Example of updated files:

pyproject.toml:
```toml
[project]
name = "docstore-manager"
version = "0.1.0"
description = "A general-purpose command-line tool for managing document stores (Qdrant and Solr)"
authors = [
    {name = "Allen Day", email = "allenday@example.com"},
]
# ... other fields ...
```

__init__.py:
```python
"""docstore-manager package."""

__version__ = "0.1.0"
```

CHANGELOG.md:
```markdown
# Changelog

## 0.1.0 (2025-05-03)

Initial release of docstore-manager.

### Features
- Support for both Qdrant and Solr document stores
- Command-line interface for managing collections and documents
- Configuration profiles for different environments
- Comprehensive documentation and examples

### Changes
- Renamed from "Qdrant Manager" to "docstore-manager"
- Added Solr support
- Standardized interfaces across document store implementations
- Improved error handling and logging
