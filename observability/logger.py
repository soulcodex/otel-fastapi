import logging
from anyio.functools import lru_cache

from opentelemetry.sdk._logs._internal.export import ConsoleLogRecordExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LogRecordProcessor, LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, SimpleLogRecordProcessor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry._logs import set_logger_provider

from observability.config import LoggerConfig


class FormattedLoggingHandler(LoggingHandler):
    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        record.msg = msg
        record.args = None
        self._logger_provider.get_logger(self.name).emit(self._translate(record))


def init_otel_logger(cfg: LoggerConfig) -> logging.Logger:
    """
    Given a logger name and a logger level, provide a OTEL compliant logger
    based on the configuration.
    """
    processor = _log_processor_from_config(cfg)
    return _init_otel_logger(cfg, processor)


def _log_processor_from_config(cfg: LoggerConfig) -> LogRecordProcessor:
    if cfg.otlp_config is not None:
        exporter = OTLPLogExporter(
            endpoint=cfg.otlp_config.endpoint,
            insecure=cfg.otlp_config.insecure,
            headers=cfg.otlp_config.headers,
        )
        return BatchLogRecordProcessor(exporter=exporter)
    return SimpleLogRecordProcessor(exporter=ConsoleLogRecordExporter())


def _init_otel_logger(
    cfg: LoggerConfig,
    log_processor: LogRecordProcessor,
) -> logging.Logger:
    """
    Given a logger name and a logger level, provide a OTEL compliant logger.
    """
    # Instrument std logger
    logger = logging.getLogger(cfg.name)
    logger.setLevel(cfg.level.value)
    LoggingInstrumentor().instrument()

    # Create a logger provider within a default resource
    logger_provider = LoggerProvider(resource=cfg.resource)
    set_logger_provider(logger_provider)

    # Register OTEL log formatter and processor (component in charge to handle log sending or generation)
    otel_log_handler = FormattedLoggingHandler(logger_provider=logger_provider)
    otel_log_handler.setFormatter(cfg.formatter)
    logger_provider.add_log_record_processor(log_processor)
    logging.getLogger().addHandler(otel_log_handler)

    return logger


@lru_cache
def provide_logger(logger_name: str) -> logging.Logger:
    """
    Provide a Logger instance.
    """
    logger_provider = logging.getLogger()
    return logger_provider.getChild(logger_name)
