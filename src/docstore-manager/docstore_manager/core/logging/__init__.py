import logging
import sys

DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logging(level=logging.INFO, log_format=DEFAULT_FORMAT) -> logging.Logger:
    """Configure basic logging and return the root logger."""
    # Use basicConfig with force=True to ensure configuration takes effect
    # even if logging was already configured elsewhere.
    logging.basicConfig(level=level, format=log_format, stream=sys.stderr, force=True)
    logger = logging.getLogger() # Get the root logger
    logger.setLevel(level)
    return logger 