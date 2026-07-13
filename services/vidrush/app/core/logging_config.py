import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Structured JSON Logging for production observability."""
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Capture the data payload if it exists (e.g. from exceptions)
        if hasattr(record, "data_payload") and record.data_payload:
            log_record["data_payload"] = record.data_payload
            
        if hasattr(record, "expected_schema") and record.expected_schema:
            log_record["expected_schema"] = record.expected_schema
            
        if hasattr(record, "failed_agent") and record.failed_agent:
            log_record["failed_agent"] = record.failed_agent

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_structured_logging():
    logger = logging.getLogger("VidRush")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
    return logger
