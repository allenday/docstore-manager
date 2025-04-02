"""
Configuration management for document store managers.
"""
from .base import (
    get_config_dir,
    get_profiles,
    load_config,
    merge_config_with_args
)

__all__ = [
    'get_config_dir',
    'get_profiles',
    'load_config',
    'merge_config_with_args'
] 