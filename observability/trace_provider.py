from anyio.functools import lru_cache
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import Tracer, TracerProvider
from opentelemetry.sdk.trace.export import SpanProcessor, SimpleSpanProcessor, BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import set_tracer_provider, get_tracer_provider

from observability.config import TracerConfig


def _processor_from_config(cfg: TracerConfig) -> SpanProcessor:
    if cfg.otlp_config is not None:
        exporter = OTLPSpanExporter(
            endpoint=cfg.otlp_config.endpoint,
            insecure=cfg.otlp_config.insecure,
            headers=cfg.otlp_config.headers,
        )
        if cfg.otlp_config.batched:
            return BatchSpanProcessor(span_exporter=exporter)
        else:
            return SimpleSpanProcessor(span_exporter=exporter)
    return SimpleSpanProcessor(ConsoleSpanExporter(service_name=cfg.service_name))


def init_otel_trace_provider(cfg: TracerConfig) -> TracerProvider:
    """
    Given a service name, provide a OTEL compliant tracer.
    """
    provider = TracerProvider(resource=cfg.resource)
    processor = _processor_from_config(cfg)
    provider.add_span_processor(processor)

    set_tracer_provider(provider)
    return provider

@lru_cache
def provide_tracer(tracer_name: str) -> Tracer:
    """
    Provide a Meter instance.
    """
    tracer_provider = get_tracer_provider()
    return tracer_provider.get_tracer(tracer_name)