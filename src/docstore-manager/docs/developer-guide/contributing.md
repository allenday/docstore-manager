# Contributing

This page provides guidelines for contributing to the docstore-manager project.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- pipx (recommended) or pip

### Setting Up the Development Environment

1. Clone the repository:

```bash
git clone https://github.com/allenday/docstore-manager.git
cd docstore-manager
```

2. Create a virtual environment and install the package in development mode:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

This will install the package in development mode along with all development dependencies.

## Development Workflow

### Branching Strategy

- `main`: The main branch contains the latest stable release
- `dev`: The development branch contains the latest development changes
- Feature branches: Create a new branch for each feature or bug fix

When working on a new feature or bug fix, create a new branch from `dev`:

```bash
git checkout dev
git pull
git checkout -b feature/your-feature-name
```

### Coding Standards

docstore-manager follows the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code. We use the following tools to enforce coding standards:

- [Black](https://black.readthedocs.io/en/stable/) for code formatting
- [isort](https://pycqa.github.io/isort/) for import sorting
- [Flake8](https://flake8.pycqa.org/en/latest/) for linting

You can run these tools using the pre-commit hooks:

```bash
pre-commit install
pre-commit run --all-files
```

### Testing

docstore-manager uses [pytest](https://docs.pytest.org/en/stable/) for testing. Tests are located in the `tests` directory.

To run the tests:

```bash
# Run unit tests
pytest

# Run integration tests (requires Qdrant and Solr to be running)
RUN_INTEGRATION_TESTS=true pytest -m integration

# Run all tests with coverage
pytest --cov=docstore_manager
```

### Documentation

docstore-manager uses [MkDocs](https://www.mkdocs.org/) with the [Material](https://squidfunk.github.io/mkdocs-material/) theme for documentation. Documentation is written in Markdown and located in the `docs` directory.

To build and serve the documentation locally:

```bash
mkdocs serve
```

Then open http://localhost:8000 in your browser.

## Pull Request Process

1. Ensure your code follows the coding standards and passes all tests
2. Update the documentation if necessary
3. Update the CHANGELOG.md file with your changes
4. Create a pull request against the `dev` branch
5. Wait for the CI/CD pipeline to run and ensure all checks pass
6. Wait for a maintainer to review your pull request
7. Address any feedback from the maintainer
8. Once approved, your pull request will be merged into the `dev` branch

## Release Process

1. Update the version number in `pyproject.toml`, `setup.py`, and `docstore_manager/__init__.py`
2. Update the CHANGELOG.md file with the new version
3. Create a pull request from `dev` to `main`
4. Once approved and merged, create a new release on GitHub
5. The CI/CD pipeline will automatically build and publish the package to PyPI

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](https://www.contributor-covenant.org/version/2/0/code_of_conduct/). By participating in this project you agree to abide by its terms.
