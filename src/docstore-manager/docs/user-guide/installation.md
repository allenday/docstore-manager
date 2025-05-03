# Installation

This guide covers how to install the docstore-manager tool and set up your environment.

## Prerequisites

- Python 3.8 or higher
- pip or pipx (recommended)

## Installation Methods

### Using pipx (Recommended)

[pipx](https://pypa.github.io/pipx/) is a tool to install and run Python applications in isolated environments. This is the recommended installation method for docstore-manager.

```bash
# Install pipx if you don't have it
python -m pip install --user pipx
python -m pipx ensurepath

# Install docstore-manager
pipx install docstore-manager
```

### Using pip

You can also install docstore-manager using pip:

```bash
pip install docstore-manager
```

### From Source

To install from source:

```bash
git clone https://github.com/allenday/docstore-manager.git
cd docstore-manager
pip install -e .
```

## Verifying Installation

After installation, verify that docstore-manager is installed correctly:

```bash
docstore-manager --version
```

This should display the version number of the installed docstore-manager.

## Next Steps

After installation, you'll need to [configure](configuration.md) docstore-manager to connect to your document stores.
