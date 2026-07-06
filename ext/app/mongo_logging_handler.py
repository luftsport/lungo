import logging
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from flask import request, g, has_request_context

class FlaskContextFilter(logging.Filter):
    """Injects Flask context data into the log record automatically."""
    def filter(self, record):
        if has_request_context():
            # Default Flask resources
            record.clientip = request.remote_addr if request else None
            record.method = request.method if request else None
            record.url = request.url if request else None

            record.client_id = getattr(g, 'client_id', None)
            if 'person_id' not in record.__dict__.keys():
                record.person_id = getattr(g, 'person_id', None)
        else:
            record.client_id = None
        return True
class SimpleMongoHandler(logging.Handler):
    def __init__(
            self,
            logs_uri: str,
            database_name,
            collection_name,
            static_fields: dict = None
    ):
        super().__init__()
        self.client = MongoClient(logs_uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]

        # Default static fields
        self.static_fields = static_fields or {
            'logger': 'eve',
            'app': 'lungo',
        }
        # Create capped collection if it doesn't exist
        if collection_name not in self.db.list_collection_names():
            self.db.create_collection(
                collection_name,
                capped=True,
                size=100 * 1024 * 1024,  # 100 MB
                max=100000
            )

    def emit(self, record):
        try:
            # Timestamp in ISO format (with timezone awareness)

            log_entry = record.__dict__.copy()  # Start with all attributes of the record
            log_entry['timestamp'] = datetime.utcnow().isoformat() + 'Z'

            # Add all static fields
            log_entry.update(self.static_fields)

            # Add extra fields from logger.error(..., extra={...}) and has not already been added to the record:
            if hasattr(record, 'extra') and isinstance(record.extra, dict):
                # Avoid overwriting core fields
                extra_clean = {k: v for k, v in record.extra.items()
                               if k not in ('timestamp', 'level', 'logger')}
                log_entry.update(extra_clean)

            # Exception info
            if record.exc_info:
                log_entry['exc_info'] = self.format(record.exc_info)

            self.collection.insert_one(log_entry)

        except PyMongoError as e:
            self.handleError(record)
        except Exception:
            self.handleError(record)


# Optional: Buffered version
class BufferedSimpleMongoHandler(SimpleMongoHandler):
    def __init__(self, logs_uri: str, buffer_size=80, **kwargs):
        super().__init__(logs_uri, **kwargs)
        self.buffer = []
        self.buffer_size = buffer_size

    def emit(self, record):
        self.buffer.append(record)
        if len(self.buffer) >= self.buffer_size or record.levelno >= logging.ERROR:
            self.flush()

    def flush(self):
        if not self.buffer:
            return
        entries = []
        for record in self.buffer:
            # Reuse logic by temporarily calling emit logic (or duplicate minimal code)
            # For simplicity, you can call super logic here if you refactor
            pass  # I'll expand if you want the full buffered version
        self.buffer.clear()