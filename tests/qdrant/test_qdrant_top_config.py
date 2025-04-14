"""Tests for Qdrant configuration management."""

import pytest
from docstore_manager.qdrant.config import QdrantConfigurationConverter

def test_convert_empty_config():
    """Test converting empty configuration."""
    converter = QdrantConfigurationConverter()
    result = converter.convert({})
    assert result == {}

def test_convert_minimal_config():
    """Test converting minimal configuration."""
    converter = QdrantConfigurationConverter()
    config = {
        "qdrant": {
            "connection": {
                "url": "http://localhost",
                "port": 6333
            }
        }
    }
    result = converter.convert(config)
    assert result["url"] == "http://localhost"
    assert result["port"] == 6333
    assert result["vector_size"] == 256  # default value
    assert result["distance"] == "cosine"  # default value
    assert result["indexing_threshold"] == 0  # default value
    assert result["payload_indices"] == []  # default value

def test_convert_full_config():
    """Test converting full configuration."""
    converter = QdrantConfigurationConverter()
    config = {
        "qdrant": {
            "connection": {
                "url": "http://localhost",
                "port": 6333,
                "api_key": "test-key",
                "collection": "test-collection"
            },
            "vectors": {
                "size": 512,
                "distance": "euclid",
                "indexing_threshold": 100
            },
            "payload_indices": ["field1", "field2"]
        }
    }
    result = converter.convert(config)
    assert result["url"] == "http://localhost"
    assert result["port"] == 6333
    assert result["api_key"] == "test-key"
    assert result["collection"] == "test-collection"
    assert result["vector_size"] == 512
    assert result["distance"] == "euclid"
    assert result["indexing_threshold"] == 100
    assert result["payload_indices"] == ["field1", "field2"]

def test_convert_partial_config():
    """Test converting partial configuration."""
    converter = QdrantConfigurationConverter()
    config = {
        "qdrant": {
            "connection": {
                "url": "http://localhost"
            },
            "vectors": {
                "size": 512
            }
        }
    }
    result = converter.convert(config)
    assert result["url"] == "http://localhost"
    assert result["port"] is None
    assert result["vector_size"] == 512
    assert result["distance"] == "cosine"  # default value
    assert result["indexing_threshold"] == 0  # default value

def test_convert_missing_sections():
    """Test converting configuration with missing sections."""
    converter = QdrantConfigurationConverter()
    config = {
        "qdrant": {}
    }
    result = converter.convert(config)
    assert result["url"] is None
    assert result["port"] is None
    assert result["vector_size"] == 256  # default value
    assert result["distance"] == "cosine"  # default value
    assert result["indexing_threshold"] == 0  # default value

def test_convert_none_config():
    """Test converting None configuration."""
    converter = QdrantConfigurationConverter()
    result = converter.convert(None)
    assert result == {} 