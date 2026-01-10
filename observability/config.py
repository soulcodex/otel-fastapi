import os
import logging

from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass, field

from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.attributes import service_attributes

DEFAULT_LOGGING_FORMAT = "%(pathname)s:%(funcName)s:%(lineno)d:%(levelname)s:%(message)s"
DEFAULT_OLTP_ENDPOINT = "http://localhost:4317"
DEFAULT_OTLP_INSECURE = "1"
DEFAULT_OTLP_HEADERS = ""

DEFAULT_METRICS_EXPORT_INTERVAL_MS = float(60000)
DEFAULT_METRICS_EXPORT_TIMEOUT_MS = float(30000)


### OTLP Exporter Configuration Dataclass ###
@dataclass(frozen=True)
class OTLPConfig:
    endpoint: str = field(default=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", DEFAULT_OLTP_ENDPOINT))
    insecure: bool = field(default=bool(int(os.getenv("OTEL_EXPORTER_OTLP_INSECURE", DEFAULT_OTLP_INSECURE))))
    headers: dict = field(
        default_factory=lambda: otlp_headers_from_env(
            {},
            os.getenv("OTEL_EXPORTER_OTLP_HEADERS", DEFAULT_OTLP_HEADERS),
        ),
    )
    batched: bool = field(default=True)


def otlp_headers_from_env(headers: Dict[str, str], raw_headers: str):
    if raw_headers:
        for header in raw_headers.split(","):
            key, value = header.split("=", 1)
            headers[key.strip()] = value.strip()
    return headers


### Logging Configuration Dataclasses ###
@dataclass(frozen=True)
class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    @classmethod
    def from_str(cls, value: str) -> LogLevel:
        return LogLevel[value.upper()]


@dataclass(frozen=True)
class LoggerConfig:
    resource: Resource
    name: str = field(default=__name__)
    level: LogLevel = field(default=logging.INFO)
    otlp_config: Optional[OTLPConfig] = field(default=None)
    formatter: logging.Formatter = field(
        default=logging.Formatter(os.getenv("OTEL_PYTHON_LOG_FORMAT", DEFAULT_LOGGING_FORMAT)),
    )

    @property
    def service_name(self) -> Optional[str]:
        return self.resource.attributes.get(service_attributes.SERVICE_NAME)


### Tracer Configuration Dataclasses ###
@dataclass(frozen=True)
class TracerConfig:
    # Service resource attributes
    resource: Resource

    # OTLP exporter configuration
    otlp_config: Optional[OTLPConfig] = field(default=None)

    @property
    def service_name(self) -> Optional[str]:
        return self.resource.attributes.get(service_attributes.SERVICE_NAME)


### Meter Configuration Dataclasses ###
@dataclass(frozen=True)
class MeterConfig:
    # Service resource attributes
    resource: Resource

    # OTLP exporter configuration
    otlp_config: Optional[OTLPConfig] = field(default=None)

    # Exporter specific configuration
    enable_prometheus_reader: bool = field(default=True)
    export_interval_milliseconds: float = field(default=DEFAULT_METRICS_EXPORT_INTERVAL_MS)
    export_timeout_milliseconds: float = field(default=DEFAULT_METRICS_EXPORT_TIMEOUT_MS)

    @property
    def service_name(self) -> Optional[str]:
        return self.resource.attributes.get(service_attributes.SERVICE_NAME)
