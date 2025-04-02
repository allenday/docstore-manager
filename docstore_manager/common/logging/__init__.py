"""
Common logging configuration for document store managers.
"""
import logging

def setup_logging(level=logging.INFO):
    """Configure logging with a common format.
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__) 