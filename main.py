import logging
import os

import uvicorn

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from metrics_router import metrics_router
from example_router import example_router
from observability.config import otlp_headers_from_env, LoggerConfig, MeterConfig, OTLPConfig, TracerConfig, LogLevel
from observability.logger import init_otel_logger
from observability.meter_provider import init_otel_meter_provider
from observability.resource_builder import ResourceBuilder
from observability.trace_provider import init_otel_trace_provider
from observability.fastapi.middleware import provide_otel_request_logger_middleware, \
    provide_otel_request_identifier_middleware
from settings import get_config, Config


def create_app() -> FastAPI:
    cfg = get_config()
    app_instance = FastAPI(title=cfg.app.doc_title, version=cfg.app.app_version)

    resource = ResourceBuilder.new(). \
        with_name(cfg.app.app_name). \
        with_version(cfg.app.app_version). \
        with_namespace(cfg.otel.service_namespace). \
        with_environment(cfg.app.environment). \
        build()

    trace_provider = configure_trace_provider(resource, cfg)
    meter_provider = configure_meter_provider(app_instance, resource, cfg)
    logger = configure_logger(resource, cfg)

    FastAPIInstrumentor().instrument_app(
        app=app_instance,
        tracer_provider=trace_provider,
        meter_provider=meter_provider,
        excluded_urls="/metrics",
    )
    logger.info("service started...")
    app_instance.include_router(example_router)
    app_instance.middleware("http")(provide_otel_request_identifier_middleware())
    app_instance.middleware("http")(provide_otel_request_logger_middleware(logger))
    return app_instance


def configure_trace_provider(resource: Resource, cfg: Config) -> TracerProvider:
    tracer_config = TracerConfig(
        resource=resource,
        otlp_config=OTLPConfig(
            endpoint=cfg.otel.otlp_endpoint,
            insecure=cfg.otel.otlp_insecure,
            headers=otlp_headers_from_env({}, cfg.otel.otlp_headers),
            batched=cfg.otel.traces_batched,
        ) if cfg.otel.trace_exporter == "otlp" and cfg.otel.otlp_enabled else None,
    )

    return init_otel_trace_provider(tracer_config)


def configure_meter_provider(app_instance: FastAPI, resource: Resource, cfg: Config) -> MeterProvider:
    meter_config = MeterConfig(
        resource=resource,
        otlp_config=OTLPConfig(
            endpoint=cfg.otel.otlp_endpoint,
            insecure=cfg.otel.otlp_insecure,
            headers=otlp_headers_from_env({}, cfg.otel.otlp_headers),
        ) if cfg.otel.metric_exporter == "otlp" and cfg.otel.otlp_enabled else None,
        enable_prometheus_reader=cfg.otel.prometheus_enabled,
    )

    meter_provider, prometheus_reader = init_otel_meter_provider(meter_config)
    if prometheus_reader is not None:
        app_instance.include_router(metrics_router)

    return meter_provider


def configure_logger(resource: Resource, cfg: Config) -> logging.Logger:
    logger_config = LoggerConfig(
        resource=resource,
        otlp_config=OTLPConfig(
            endpoint=cfg.otel.otlp_endpoint,
            insecure=cfg.otel.otlp_insecure,
            headers=otlp_headers_from_env({}, cfg.otel.otlp_headers),
        ) if cfg.otel.log_exporter == "otlp" and cfg.otel.otlp_enabled else None,
        name=cfg.app.app_name,
        level=LogLevel.from_str(cfg.logger.level),
        formatter=logging.Formatter(os.getenv("OTEL_PYTHON_LOG_FORMAT", cfg.logger.format)),
    )

    return init_otel_logger(logger_config)


if __name__ == "__main__":
    config = get_config()
    uvicorn.run(
        app='main:create_app',
        factory=True,
        host=config.http.host,
        port=config.http.port,
        reload=config.app.is_debug_mode(),
        reload_includes=["*.py", ".env"] if config.app.is_debug_mode() else None,
        timeout_graceful_shutdown=config.app.graceful_shutdown_timeout,
        access_log=False,
        log_level=config.logger.level,
    )
