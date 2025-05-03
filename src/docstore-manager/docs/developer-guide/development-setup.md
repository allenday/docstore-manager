# Development Setup

This page provides detailed instructions for setting up a development environment for docstore-manager.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.8 or higher
- Git
- Docker and Docker Compose (for running Qdrant and Solr locally)
- pipx (recommended) or pip

## Clone the Repository

```bash
git clone https://github.com/allenday/docstore-manager.git
cd docstore-manager
```

## Create a Virtual Environment

It's recommended to use a virtual environment for development:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

## Install Development Dependencies

Install the package in development mode along with all development dependencies:

```bash
pip install -e ".[dev]"
```

This will install:

- The package itself in development mode
- All runtime dependencies
- Development dependencies (pytest, black, isort, flake8, etc.)
- Documentation dependencies (mkdocs, mkdocs-material, etc.)

## Set Up Pre-commit Hooks

docstore-manager uses pre-commit hooks to enforce coding standards:

```bash
pre-commit install
```

This will install pre-commit hooks that run automatically when you commit changes.

## Run Tests

docstore-manager has two types of tests:

- Unit tests: These don't require external services and can be run quickly
- Integration tests: These require Qdrant and Solr to be running

### Running Unit Tests

```bash
pytest
```

### Running Integration Tests

First, start Qdrant and Solr using Docker Compose:

```bash
docker-compose up -d
```

Then run the integration tests:

```bash
RUN_INTEGRATION_TESTS=true pytest -m integration
```

### Running All Tests with Coverage

```bash
pytest --cov=docstore_manager
```

## Build Documentation

docstore-manager uses MkDocs with the Material theme for documentation:

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build and serve documentation locally
mkdocs serve
```

Then open http://localhost:8000 in your browser.

## Development Workflow

1. Create a new branch for your feature or bug fix:

```bash
git checkout dev
git pull
git checkout -b feature/your-feature-name
```

2. Make your changes and commit them:

```bash
git add .
git commit -m "Your commit message"
```

3. Push your changes to GitHub:

```bash
git push -u origin feature/your-feature-name
```

4. Create a pull request on GitHub against the `dev` branch.

## Running Qdrant and Solr Locally

docstore-manager includes a Docker Compose file for running Qdrant and Solr locally:

```bash
# Start Qdrant and Solr
docker-compose up -d

# Stop Qdrant and Solr
docker-compose down
```

### Qdrant

Qdrant will be available at http://localhost:6333.

### Solr

Solr will be available at http://localhost:8983/solr.

## Troubleshooting

### Common Issues

#### ImportError: No module named 'docstore_manager'

This can happen if you haven't installed the package in development mode. Run:

```bash
pip install -e .
```

#### Pre-commit hooks fail

If pre-commit hooks fail, you can fix the issues and try again:

```bash
pre-commit run --all-files
```

#### Integration tests fail

If integration tests fail, make sure Qdrant and Solr are running:

```bash
docker-compose ps
```

If they're not running, start them:

```bash
docker-compose up -d
```

#### Documentation doesn't build

If the documentation doesn't build, make sure you have the documentation dependencies installed:

```bash
pip install -e ".[docs]"
```
