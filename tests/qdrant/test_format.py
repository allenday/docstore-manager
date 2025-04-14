"""Tests for Qdrant response formatter."""

import pytest
from docstore_manager.qdrant.format import QdrantFormatter

@pytest.fixture
def formatter():
    """Create a formatter instance."""
    return QdrantFormatter()

def test_format_collection_list(formatter):
    """Test formatting a list of collections."""
    collections = [
        {
            "name": "test1",
            "vectors_config": {
                "size": 128,
                "distance": "cosine"
            },
            "points_count": 100,
            "status": "green"
        },
        {
            "name": "test2",
            "vectors_config": {
                "size": 256,
                "distance": "euclid"
            }
            # Missing optional fields
        }
    ]
    
    result = formatter.format_collection_list(collections)
    assert isinstance(result, str)
    
    # The result should be a JSON string, so we can parse it back
    import json
    parsed = json.loads(result)
    
    assert len(parsed) == 2
    assert parsed[0]["name"] == "test1"
    assert parsed[0]["vectors"]["size"] == 128
    assert parsed[0]["vectors"]["distance"] == "cosine"
    assert parsed[0]["points_count"] == 100
    assert parsed[0]["status"] == "green"
    
    assert parsed[1]["name"] == "test2"
    assert parsed[1]["vectors"]["size"] == 256
    assert parsed[1]["vectors"]["distance"] == "euclid"
    assert parsed[1]["points_count"] == 0  # Default value
    assert parsed[1]["status"] == "unknown"  # Default value

def test_format_collection_info(formatter):
    """Test formatting collection information."""
    info = {
        "name": "test",
        "vectors_config": {
            "size": 128,
            "distance": "cosine"
        },
        "points_count": 100,
        "status": "green",
        "on_disk_payload": True,
        "hnsw_config": {"m": 16, "ef_construct": 100},
        "optimizers_config": {"deleted_threshold": 0.1},
        "wal_config": {"wal_capacity_mb": 32}
    }
    
    result = formatter.format_collection_info(info)
    assert isinstance(result, str)
    
    import json
    parsed = json.loads(result)
    
    assert parsed["name"] == "test"
    assert parsed["vectors"]["size"] == 128
    assert parsed["vectors"]["distance"] == "cosine"
    assert parsed["points_count"] == 100
    assert parsed["status"] == "green"
    assert parsed["config"]["on_disk"] is True
    assert parsed["config"]["hnsw_config"] == {"m": 16, "ef_construct": 100}
    assert parsed["config"]["optimizers_config"] == {"deleted_threshold": 0.1}
    assert parsed["config"]["wal_config"] == {"wal_capacity_mb": 32}

def test_format_collection_info_minimal(formatter):
    """Test formatting collection information with minimal fields."""
    info = {
        "name": "test",
        "vectors_config": {
            "size": 128,
            "distance": "cosine"
        }
    }
    
    result = formatter.format_collection_info(info)
    assert isinstance(result, str)
    
    import json
    parsed = json.loads(result)
    
    assert parsed["name"] == "test"
    assert parsed["vectors"]["size"] == 128
    assert parsed["vectors"]["distance"] == "cosine"
    assert parsed["points_count"] == 0  # Default value
    assert parsed["status"] == "unknown"  # Default value
    assert parsed["config"]["on_disk"] is False  # Default value
    assert parsed["config"]["hnsw_config"] == {}  # Default value
    assert parsed["config"]["optimizers_config"] == {}  # Default value
    assert parsed["config"]["wal_config"] == {}  # Default value

def test_format_documents(formatter):
    """Test formatting documents."""
    documents = [
        {
            "id": "1",
            "payload": {"text": "test1"},
            "vector": [1.0, 2.0],
            "score": 0.9
        },
        {
            "id": "2",
            "payload": {"text": "test2"},
            "vector": [3.0, 4.0]
            # No score
        }
    ]
    
    # Test without vectors
    result = formatter.format_documents(documents)
    assert isinstance(result, str)
    
    import json
    parsed = json.loads(result)
    
    assert len(parsed) == 2
    assert parsed[0]["id"] == "1"
    assert parsed[0]["payload"] == {"text": "test1"}
    assert parsed[0]["score"] == 0.9
    assert "vector" not in parsed[0]
    
    assert parsed[1]["id"] == "2"
    assert parsed[1]["payload"] == {"text": "test2"}
    assert "score" not in parsed[1]
    assert "vector" not in parsed[1]
    
    # Test with vectors
    result = formatter.format_documents(documents, with_vectors=True)
    assert isinstance(result, str)
    
    parsed = json.loads(result)
    
    assert len(parsed) == 2
    assert parsed[0]["id"] == "1"
    assert parsed[0]["payload"] == {"text": "test1"}
    assert parsed[0]["score"] == 0.9
    assert parsed[0]["vector"] == [1.0, 2.0]
    
    assert parsed[1]["id"] == "2"
    assert parsed[1]["payload"] == {"text": "test2"}
    assert "score" not in parsed[1]
    assert parsed[1]["vector"] == [3.0, 4.0]

def test_format_documents_minimal(formatter):
    """Test formatting documents with minimal fields."""
    documents = [
        {
            "id": "1"
            # No payload, vector or score
        }
    ]
    
    result = formatter.format_documents(documents)
    assert isinstance(result, str)
    
    import json
    parsed = json.loads(result)
    
    assert len(parsed) == 1
    assert parsed[0]["id"] == "1"
    assert parsed[0]["payload"] == {} 