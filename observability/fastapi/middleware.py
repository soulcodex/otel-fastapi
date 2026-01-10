import http
import time
import uuid
import logging
from typing import Awaitable, Callable, Literal

from fastapi import Request, Response
from fastapi.types import DecoratedCallable
from opentelemetry import trace
from opentelemetry.semconv._incubating.attributes import http_attributes, url_attributes
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

tracer = trace.get_tracer(__name__)

type CallNext = Callable[[Request], Awaitable[Response]]

CorrelationIdAttribute: Literal["correlation_id"] = "correlation_id"
CorrelationIdRequestHeader: Literal["X-Request-Id"] = "X-Request-Id"
CorrelationIdResponseHeader: Literal["X-Response-Id"] = "X-Response-Id"


def provide_otel_request_logger_middleware(logger: logging.Logger) -> DecoratedCallable:
    async def _middleware(request: Request, call_next: CallNext) -> Response:
        start = time.perf_counter()
        response: Response | None = None

        try:
            response = await call_next(request)
            return response
        finally:
            duration = (time.perf_counter() - start) * 1000
            status_code = (
                response.status_code
                if response is not None
                else http.HTTPStatus.INTERNAL_SERVER_ERROR
            )

            log_extra_attrs = {
                http_attributes.HTTP_METHOD:               request.method,
                url_attributes.URL_PATH:                   request.url.path,
                http_attributes.HTTP_RESPONSE_STATUS_CODE: int(status_code),
                "http.server.duration_ms":                 round(duration, 2),
                "request_id":                              getattr(request.state, CorrelationIdAttribute, None),
                "correlation_id":                          getattr(request.state, CorrelationIdAttribute, None),
            }

            span = trace.get_current_span()
            if span.is_recording():
                ctx = span.get_span_context()
                log_extra_attrs["trace_id"] = format(ctx.trace_id, "032x")
                log_extra_attrs["span_id"] = format(ctx.span_id, "016x")
                log_extra_attrs["traceflags"] = int(ctx.trace_flags)
                log_extra_attrs["traceparent"] = _get_traceparent_header()

            logger.info("HTTP request", extra=log_extra_attrs)

    return _middleware


def provide_otel_request_identifier_middleware() -> DecoratedCallable:
    async def _middleware(request: Request, call_next: CallNext) -> Response:
        request_id = request.headers.get(CorrelationIdRequestHeader, str(uuid.uuid4()))
        request.state.__setattr__(CorrelationIdAttribute, request_id)

        response: Response = await call_next(request)
        response.headers[CorrelationIdResponseHeader] = request_id

        return response

    return _middleware


def _get_traceparent_header() -> str | None:
    carrier = {}
    TraceContextTextMapPropagator().inject(carrier)
    if "traceparent" in carrier:
        return carrier["traceparent"]
    return None
