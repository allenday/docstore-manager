"""Tests for Solr configuration."""

import pytest
from docstore_manager.solr.config import SolrConfigurationConverter

@pytest.fixture
def converter():
    return SolrConfigurationConverter()

def test_convert_full_config(converter):
    """Test converting a profile with full Solr configuration."""
    profile_config = {
        "solr": {
            "connection": {
                "solr_url": "http://solr:8983/solr",
                "collection": "my_coll",
                "zk_hosts": "zk1:2181,zk2:2181/solr",
                "num_shards": 2,
                "replication_factor": 3,
                "config_name": "custom_config",
                "max_shards_per_node": 5
            }
        },
        "other_setting": "value"
    }
    expected = {
        "solr_url": "http://solr:8983/solr",
        "collection": "my_coll",
        "zk_hosts": "zk1:2181,zk2:2181/solr",
        "num_shards": 2,
        "replication_factor": 3,
        "config_name": "custom_config",
        "max_shards_per_node": 5
    }
    assert converter.convert(profile_config) == expected

def test_convert_missing_solr_section(converter):
    """Test converting a profile missing the 'solr' section."""
    profile_config = {"other_setting": "value"}
    # Should default to None for required fields, use defaults for others
    expected = {
        "solr_url": None,
        "collection": None,
        "zk_hosts": None,
        "num_shards": 1,
        "replication_factor": 1,
        "config_name": "_default",
        "max_shards_per_node": -1
    }
    assert converter.convert(profile_config) == expected

def test_convert_missing_connection_section(converter):
    """Test converting a profile with 'solr' but missing 'connection'."""
    profile_config = {"solr": {"other_solr_key": "val"}}
    expected = {
        "solr_url": None,
        "collection": None,
        "zk_hosts": None,
        "num_shards": 1,
        "replication_factor": 1,
        "config_name": "_default",
        "max_shards_per_node": -1
    }
    assert converter.convert(profile_config) == expected

def test_convert_missing_optional_keys(converter):
    """Test converting a profile with only required keys."""
    profile_config = {
        "solr": {
            "connection": {
                "solr_url": "http://minimal:8983/solr"
            }
        }
    }
    expected = {
        "solr_url": "http://minimal:8983/solr",
        "collection": None,
        "zk_hosts": None,
        "num_shards": 1, # default
        "replication_factor": 1, # default
        "config_name": "_default", # default
        "max_shards_per_node": -1 # default
    }
    assert converter.convert(profile_config) == expected

def test_convert_empty_profile(converter):
    """Test converting an empty profile configuration."""
    profile_config = {}
    # Should return empty dict
    assert converter.convert(profile_config) == {}

def test_convert_none_profile(converter):
    """Test converting a None profile configuration."""
    profile_config = None
    # Should return empty dict
    assert converter.convert(profile_config) == {} 