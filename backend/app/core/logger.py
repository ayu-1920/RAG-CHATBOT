import logging
import sys

def setup_logger():
    """
    Configures a centralized, production-grade logger for the backend application.
    
    [Interview Design Note]: 
    Beginners typically use `print()` statements implicitly across files, which is untraceable 
    in cloud environments (AWS CloudWatch, Datadog). Extracting a central logger provides 
    standardized formatting, thread safety, and log-level manipulation across the microservice.
    """
    logger = logging.getLogger("rag_api")
    logger.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] [%(funcName)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    stream_handler.setFormatter(formatter)
    
    # Prevent handler duplication if the module is reloaded
    if not logger.handlers:
        logger.addHandler(stream_handler)
        
    return logger

logger = setup_logger()
