# Changelog

All notable changes to the docstore-manager project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-05-04

### Added
- Additional documentation examples
- Improved error messages

### Changed
- Updated dependency requirements
- Enhanced documentation

### Fixed
- Minor bug fixes and improvements

## [0.1.0] - 2025-05-03

Initial release of docstore-manager.

### Added
- Support for both Qdrant and Solr document stores
- Comprehensive usage examples for all operations
- Improved error handling and logging
- Standardized interfaces across document store implementations
- Configuration profiles for different environments
- Command-line interface for managing collections and documents
- Detailed documentation and API reference

### Changed
- Renamed from "Qdrant Manager" to "docstore-manager"
- Consolidated CLI entry points to a single `docstore-manager` command
- Improved test coverage and reliability
- Enhanced formatting options for command outputs

### Fixed
- Collection info formatting issues
- CLI testing context handling
- Parameter validation in get_documents function
- CollectionConfig validation
