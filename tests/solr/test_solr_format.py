"""Tests for Solr Formatter."""

import pytest
import json

from docstore_manager.solr.format import SolrFormatter

# Assume base class _format_output simply returns json.dumps for testing
class TestableSolrFormatter(SolrFormatter):
    def _format_output(self, data) -> str:
        return json.dumps(data, indent=2)

@pytest.fixture
def formatter():
    return TestableSolrFormatter()

# --- format_collection_list Tests ---

def test_format_collection_list_basic(formatter):
    collections = [
        {"name": "coll1", "configName": "conf1", "shards": {"s1": {}}, "replicas": {"r1": {}}, "health": "green"},
        {"name": "coll2", "configName": "conf2"} # Missing optional keys
    ]
    expected = [
        {"name": "coll1", "config": "conf1", "shards": {"s1": {}}, "replicas": {"r1": {}}, "status": "green"},
        {"name": "coll2", "config": "conf2", "shards": {}, "replicas": {}, "status": "unknown"}
    ]
    result = formatter.format_collection_list(collections)
    assert json.loads(result) == expected

def test_format_collection_list_empty(formatter):
    result = formatter.format_collection_list([])
    assert json.loads(result) == []

# --- format_collection_info Tests ---

def test_format_collection_info_basic(formatter):
    info = {
        "name": "info_coll",
        "numShards": 2,
        "replicationFactor": 2,
        "configName": "_default",
        "router": {"name": "compositeId", "field": "id"},
        "shards": {"shard1": {}},
        "aliases": ["alias1"],
        "properties": {"prop1": "val1"}
    }
    expected = {
        "name": "info_coll",
        "num_shards": 2,
        "replication_factor": 2,
        "config": "_default",
        "router": {"name": "compositeId", "field": "id"},
        "shards": {"shard1": {}},
        "aliases": ["alias1"],
        "properties": {"prop1": "val1"}
    }
    result = formatter.format_collection_info(info)
    assert json.loads(result) == expected

def test_format_collection_info_missing_optional(formatter):
    info = {"name": "minimal_coll"}
    expected = {
        "name": "minimal_coll",
        "num_shards": 0, 
        "replication_factor": 0,
        "config": "unknown",
        "router": {"name": "unknown", "field": None},
        "shards": {},
        "aliases": [],
        "properties": {}
    }
    result = formatter.format_collection_info(info)
    assert json.loads(result) == expected

# --- format_documents Tests ---

def test_format_documents_basic(formatter):
    docs = [
        {"id": "doc1", "field": "val1", "_version_": 123, "_score_": 1.5, "_vector_": [0.1, 0.2]},
        {"id": "doc2", "field": "val2", "_version_": 456} # No score or vector
    ]
    # Default: with_vectors=False
    expected = [
        {"id": "doc1", "field": "val1", "score": 1.5},
        {"id": "doc2", "field": "val2"}
    ]
    result = formatter.format_documents(docs)
    assert json.loads(result) == expected

def test_format_documents_with_vectors(formatter):
    docs = [
        {"id": "doc1", "field": "val1", "_version_": 123, "_score_": 1.5, "_vector_": [0.1, 0.2]},
    ]
    expected = [
        {"id": "doc1", "field": "val1", "score": 1.5, "_vector_": [0.1, 0.2]},
    ]
    result = formatter.format_documents(docs, with_vectors=True)
    assert json.loads(result) == expected

def test_format_documents_empty(formatter):
    result = formatter.format_documents([])
    assert json.loads(result) == [] 