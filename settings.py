import os
from anyio.functools import lru_cache
from typing import Literal, Sequence

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_file_paths(file_names: Sequence[str]) -> Sequence[str]:
    return [os.path.join(os.path.dirname(__file__), file_name) for file_name in file_names]


class ApplicationSettings(BaseModel):
    doc_title: str = Field(default="OTEL FastAPI Example")
    environment: Literal['local', 'test', 'dev', 'stg', 'prod'] = Field(default="dev")
    app_name: str = Field(default="otel-fastapi-example")
    app_version: str = Field(default="0.1.0")
    graceful_shutdown_timeout: int = Field(default=30)  # seconds

    def is_debug_mode(self) -> bool:
        return self.environment in ['local', 'test']


class LoggerSettings(BaseModel):
    type: str = Field(default="console")
    name: str = Field(default="otel-fastapi-example")
    level: str = Field(default="INFO")
    format: str = Field(default="%(message)s")


class HTTPSettings(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)


class OTELSettings(BaseModel):
    trace_exporter: str = Field(default="console")  # options: otlp, console, none
    metric_exporter: str = Field(default="console")  # options: otlp, console, none
    log_exporter: str = Field(default="console")  # options: otlp, console, none

    otlp_enabled: bool = Field(default=True)
    otlp_endpoint: str = Field(default="http://localhost:4317")
    otlp_headers: str = Field(default="")
    otlp_insecure: bool = Field(default=False)
    traces_batched: bool = Field(default=True)
    prometheus_enabled: bool = Field(default=True)
    service_namespace: str = Field(default="otel-fastapi-example")


class Config(BaseSettings):
    app: ApplicationSettings = Field(default_factory=ApplicationSettings)
    http: HTTPSettings = Field(default_factory=HTTPSettings)
    logger: LoggerSettings = Field(default_factory=LoggerSettings)
    otel: OTELSettings = Field(default_factory=OTELSettings)

    model_config = SettingsConfigDict(
        env_file=_env_file_paths([".env", ".env.local", ".env.test"]),
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter='__',
    )


@lru_cache
def get_config() -> Config:
    return Config()
