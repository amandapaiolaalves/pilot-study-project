import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        context = {
            key: value
            for key, value in record.__dict__.items()
            if key not in vars(logging.LogRecord("", 0, "", 0, "", (), None))
            and not key.startswith("_")
        }
        if context:
            payload["context"] = context

        return json.dumps(payload, ensure_ascii=False)


class MongoDBLogHandler(logging.Handler):
    def __init__(
        self,
        uri: str,
        database: str,
        collection: str,
        tls_ca_file: str | None = None,
    ):
        super().__init__()
        client_options: dict[str, Any] = {
            "serverSelectionTimeoutMS": 2_000,
            "connectTimeoutMS": 2_000,
        }
        if tls_ca_file:
            client_options["tlsCAFile"] = tls_ca_file
        self._client = MongoClient(
            uri,
            **client_options,
        )
        self._collection = self._client[database][collection]

    def emit(self, record: logging.LogRecord) -> None:
        try:
            document: dict[str, Any] = {
                "timestamp": datetime.fromtimestamp(
                    record.created, tz=timezone.utc
                ),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            if record.exc_info:
                document["exception"] = self.formatException(record.exc_info)

            standard_fields = set(
                vars(logging.LogRecord("", 0, "", 0, "", (), None))
            )
            document["context"] = {
                key: value
                for key, value in record.__dict__.items()
                if key not in standard_fields and not key.startswith("_")
            }
            self._collection.insert_one(document)
        except PyMongoError:
            self.handleError(record)

    def close(self) -> None:
        self._client.close()
        super().close()


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if getattr(root_logger, "_pilot_logging_configured", False):
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root_logger.setLevel(level)

    formatter = JSONFormatter()
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    uri = os.getenv("MONGODB_URI")
    if uri:
        mongo_handler = MongoDBLogHandler(
            uri=uri,
            database=os.getenv("MONGODB_DATABASE", "pilot_study"),
            collection=os.getenv("MONGODB_LOG_COLLECTION", "application_logs"),
            tls_ca_file=os.getenv("MONGODB_TLS_CA_FILE"),
        )
        mongo_handler.setLevel(level)
        root_logger.addHandler(mongo_handler)

    root_logger._pilot_logging_configured = True
    logging.getLogger(__name__).info(
        "Logging configured",
        extra={"mongodb_enabled": bool(uri)},
    )
