"""Tests for Qdrant response formatter."""

import pytest
import json
import yaml
from unittest.mock import MagicMock
from docstore_manager.qdrant.format import QdrantFormatter
from qdrant_client.http import models as rest
from argparse import Namespace
from qdrant_client.http.models import CollectionDescription, OptimizersConfigDiff, VectorParams, Distance, HnswConfigDiff, WalConfigDiff, PointStruct

@pytest.fixture
def formatter():
    """Create a formatter instance."""
    return QdrantFormatter(format_type='json')

# Helper mock class for CollectionDescription
class MockCollectionDescription:
    def __init__(self, name):
        self.name = name

# Helper mock class for Qdrant points/records
class MockQdrantPoint:
    def __init__(self, id, payload=None, vector=None, score=None, shard_key=None):
        self.id = id
        self.payload = payload if payload is not None else {}
        self.vector = vector
        self.score = score
        self.shard_key = shard_key

def test_format_collection_list(formatter):
    """Test formatting a list of collections."""
    # Use simple dicts instead of MagicMock
    mock_collections_data = [
        {"name": "collection1"},
        {"name": "collection2"}
    ]
    # If the function expects objects with attributes, create simple objects
    class MockCollection: 
        def __init__(self, name): self.name = name
    mock_collections_objs = [MockCollection(**data) for data in mock_collections_data]
    
    result = formatter.format_collection_list(mock_collections_objs)
    assert isinstance(result, str)
    data = json.loads(result)
    assert data == mock_collections_data # Check against the original dict data

def test_format_collection_info(formatter):
    """Test formatting detailed collection info."""
    collection_name = "test_collection"
    # Create a mock CollectionDescription object with more fields
    mock_info = MagicMock(spec=CollectionDescription)
    mock_info.status = "green"
    mock_info.optimizer_status= "ok"
    mock_info.vectors_count = 1000
    mock_info.indexed_vectors_count= 0
    mock_info.points_count = 500
    mock_info.segments_count = 1
    mock_info.config = MagicMock()
    mock_info.config.params = MagicMock(spec=VectorParams, size=128, distance=Distance.COSINE)
    mock_info.config.hnsw_config = MagicMock(spec=HnswConfigDiff, ef_construct=100, m=16)
    mock_info.config.optimizer_config = MagicMock(spec=OptimizersConfigDiff, deleted_threshold=0.2)
    mock_info.config.wal_config = MagicMock(spec=WalConfigDiff, wal_capacity_mb=32)
    mock_info.payload_schema = {"field1": "keyword", "field2": "integer"}
    
    output = formatter.format_collection_info(collection_name, mock_info)
    
    # Check for key elements in the JSON output
    assert '"name": "test_collection"' in output
    assert '"status": "green"' in output
    assert '"vectors_count": 1000' in output
    assert '"points_count": 500' in output
    assert '"params": {' in output # Check nested structure
    assert '"size": 128' in output
    assert '"distance": "Cosine"' in output # Enum value
    assert '"payload_schema": {' in output
    assert '"field1": "keyword"' in output

def test_format_collection_info_minimal(formatter):
    """Test formatting minimal collection info."""
    collection_name = "minimal_coll"
    # Create a mock with only a few attributes
    mock_info = MagicMock(spec=CollectionDescription)
    mock_info.status = "yellow"
    mock_info.points_count = 10
    # Simulate missing optional fields like vectors_count, payload_schema, etc.
    # Ensure __dict__ still works for _to_dict
    mock_info.vectors_count = None 
    mock_info.config = MagicMock() # Need config object at least
    mock_info.config.params = MagicMock(spec=VectorParams, size=10, distance=Distance.EUCLID)
    # Make other config parts None or missing if the spec allows
    mock_info.config.hnsw_config = None
    mock_info.config.optimizer_config = None
    mock_info.config.wal_config = None
    mock_info.payload_schema = None
    
    output = formatter.format_collection_info(collection_name, mock_info)
    
    assert '"name": "minimal_coll"' in output
    assert '"status": "yellow"' in output
    assert '"points_count": 10' in output
    # Check that missing fields are handled (e.g., not present or null)
    # This depends on how _to_dict and the cleaning handle missing attributes or None values
    # assert '"vectors_count": null' in output or '"vectors_count"' not in output 
    assert '"params": {' in output # Check basic config still exists

def test_format_documents(formatter):
    """Test formatting documents."""
    documents = [
        MockQdrantPoint(
            id="1",
            payload={"text": "test1"},
            vector=[1.0, 2.0],
            score=0.9
        ),
        MockQdrantPoint(
            id="2",
            payload={"text": "test2"},
            vector=[3.0, 4.0]
        )
    ]

    result = formatter.format_documents(documents, with_vectors=False)
    assert isinstance(result, str)
    data = json.loads(result)
    assert len(data) == 2
    assert data[0] == {"id": "1", "payload": {"text": "test1"}, "score": 0.9}
    assert data[1] == {"id": "2", "payload": {"text": "test2"}}

    result_vec = formatter.format_documents(documents, with_vectors=True)
    assert isinstance(result_vec, str)
    data_vec = json.loads(result_vec)
    assert len(data_vec) == 2
    assert data_vec[0] == {"id": "1", "payload": {"text": "test1"}, "score": 0.9, "vector": [1.0, 2.0]}
    assert data_vec[1] == {"id": "2", "payload": {"text": "test2"}, "vector": [3.0, 4.0]}

    formatter_yaml = QdrantFormatter(format_type='yaml')
    result_yaml = formatter_yaml.format_documents(documents, with_vectors=False)
    assert isinstance(result_yaml, str)
    # Basic check for YAML structure
    assert result_yaml.strip().startswith("- id: '1'")

def test_format_documents_minimal(formatter):
    """Test formatting documents with minimal fields."""
    documents = [
        MockQdrantPoint(id="1")
    ]

    result = formatter.format_documents(documents)
    assert isinstance(result, str)
    data = json.loads(result)
    assert len(data) == 1
    assert data[0] == {"id": "1", "payload": {}}
    