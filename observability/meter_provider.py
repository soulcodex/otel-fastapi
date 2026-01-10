from typing import List, Tuple, Optional

from anyio.functools import lru_cache
from opentelemetry.sdk.metrics import Meter, MeterProvider
from opentelemetry.metrics import set_meter_provider, get_meter_provider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, \
    ConsoleMetricExporter, \
    MetricExporter, \
    MetricReader
from opentelemetry.semconv.schemas import Schemas

from observability.config import MeterConfig


def _exporter_from_config(cfg: MeterConfig) -> MetricExporter:
    if cfg.otlp_config is not None:
        exporter = OTLPMetricExporter(
            endpoint=cfg.otlp_config.endpoint,
            insecure=cfg.otlp_config.insecure,
            headers=cfg.otlp_config.headers,
        )
        return exporter
    return ConsoleMetricExporter()


def init_otel_meter_provider(cfg: MeterConfig) -> Tuple[MeterProvider, Optional[PrometheusMetricReader]]:
    """
    Initialize the OTEL Meter Provider.
    """
    exporter = _exporter_from_config(cfg)

    readers: List[MetricReader] = [
        PeriodicExportingMetricReader(
            exporter=exporter,
            export_interval_millis=cfg.export_interval_milliseconds,
            export_timeout_millis=cfg.export_timeout_milliseconds,
        )
    ]

    prometheus_reader: Optional[PrometheusMetricReader] = None

    if cfg.enable_prometheus_reader:
        prometheus_reader = PrometheusMetricReader()
        readers.append(prometheus_reader)

    meter_provider = MeterProvider(
        resource=cfg.resource,
        metric_readers=readers,
    )

    set_meter_provider(meter_provider)

    return meter_provider, prometheus_reader


@lru_cache
def provide_meter(meter_name: str) -> Meter:
    """
    Provide a Meter instance.
    """
    meter_provider = get_meter_provider()
    meter = meter_provider.get_meter(name=meter_name)
    return meter
