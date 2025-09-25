import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime
import os

def setup_logger(name: str, level: str = "INFO"):
    """
    Set up a JSON logger for production-ready logging
    """
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # JSON formatter
    formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s",
        timestamp=True
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(
        f"logs/{datetime.now().strftime('%Y%m%d')}_agent.log"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Create default logger
logger = setup_logger("workflow_agent", os.getenv("LOG_LEVEL", "INFO"))
