"""Structured JSON log formatter for Docker stdout aggregation."""

import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line for CloudWatch / Docker log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Promote common structured fields from logger.extra into the JSON root.
        for key in ("event", "duration_ms", "path", "method", "status_code", "error", "job_id"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)
