# Task: Prepare PyPI Package
**Parent:** `implementation_plan_release_prep.md`
**Children:** None

## Objective
Configure setuptools in pyproject.toml, create necessary package files, and test the build process to prepare the docstore-manager project for distribution on PyPI.

## Context
The docstore-manager project is preparing for its 0.1.0 release to PyPI. Proper package configuration is essential for ensuring that users can easily install and use the package. This task involves configuring setuptools in pyproject.toml, creating necessary package files, and testing the build process to ensure that the package can be successfully built and installed.

## Steps
1. Review the current package configuration
   - Check if pyproject.toml exists and contains package configuration
   - Check if setup.py exists and contains package configuration
   - Identify any missing or incomplete configuration

2. Configure setuptools in pyproject.toml
   - Define package metadata
     - name: "docstore-manager"
     - version: "0.1.0" (should be updated in the Update Version Number task)
     - description: A brief description of the package
     - long_description: A longer description, typically from README.md
     - author: Author name and email
     - license: The package license (e.g., Apache-2.0)
     - classifiers: PyPI classifiers for the package
     - keywords: Keywords for the package
   - Specify dependencies
     - runtime dependencies (install_requires)
     - development dependencies (dev-dependencies)
     - test dependencies (test-dependencies)
   - Configure entry points
     - Define the CLI entry point for the docstore-manager command
     - Define any other entry points needed

3. Create or update necessary package files
   - Ensure README.md is complete and up-to-date
   - Ensure LICENSE file exists and is correct
   - Create or update MANIFEST.in if needed
     - Include non-Python files that should be part of the package
     - Exclude files that should not be part of the package
   - Create or update .gitignore to exclude build artifacts

4. Configure package discovery
   - Ensure that all Python packages are properly discovered
   - Configure package_dir if needed
   - Configure packages parameter if needed

5. Test the build process
   - Install build dependencies (pip install build)
   - Build the package (python -m build)
   - Verify the package structure
     - Check that the wheel file is created
     - Check that the source distribution is created
     - Verify that all necessary files are included

6. Test installation from the built package
   - Create a virtual environment for testing
   - Install the built wheel file
   - Verify that the package can be imported
   - Verify that the CLI command works

7. Configure GitHub Actions for CI/CD
   - Create a workflow file for testing
   - Create a workflow file for building and publishing
   - Configure PyPI credentials as GitHub secrets

8. Document the release process
   - Create a RELEASE.md file with instructions for releasing
   - Include steps for updating version, building, and publishing

## Dependencies
- Requires: None
- Blocks: None

## Expected Output
1. Properly configured pyproject.toml with all necessary metadata, dependencies, and entry points
2. All necessary package files (README.md, LICENSE, MANIFEST.in, etc.)
3. Successful package build with wheel and source distribution
4. Verified installation from the built package
5. GitHub Actions workflows for CI/CD
6. Documentation for the release process

Example pyproject.toml configuration:
```toml
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "docstore-manager"
version = "0.1.0"
description = "A general-purpose command-line tool for managing document stores (Qdrant and Solr)"
readme = "README.md"
authors = [
    {name = "Allen Day", email = "allenday@example.com"},
]
license = {text = "Apache-2.0"}
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Database",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
keywords = ["qdrant", "solr", "vector database", "document store", "cli"]
requires-python = ">=3.8"
dependencies = [
    "click>=8.0.0",
    "pyyaml>=6.0",
    "qdrant-client>=1.0.0",
    "pysolr>=3.9.0",
    "rich>=12.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "pylint>=2.17.0",
    "mypy>=1.0.0",
    "isort>=5.12.0",
    "pre-commit>=3.0.0",
]
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]

[project.urls]
"Homepage" = "https://github.com/allenday/docstore-manager"
"Bug Tracker" = "https://github.com/allenday/docstore-manager/issues"
"Documentation" = "https://github.com/allenday/docstore-manager#readme"

[project.scripts]
docstore-manager = "docstore_manager.cli:main"

[tool.setuptools]
packages = ["docstore_manager"]

[tool.black]
line-length = 88
target-version = ["py38"]

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
```

Example GitHub Actions workflow for testing:
```yaml
name: Tests

on:
  push:
    branches: [ main, release-* ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install -e ".[test]"
    - name: Run tests
      run: |
        pytest --cov=docstore_manager tests/
```

Example GitHub Actions workflow for publishing:
```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build and publish
      env:
        TWINE_USERNAME: ${{ secrets.PYPI_USERNAME }}
        TWINE_PASSWORD: ${{ secrets.PYPI_PASSWORD }}
      run: |
        python -m build
        twine upload dist/*
