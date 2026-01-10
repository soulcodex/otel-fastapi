from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

metrics_router = APIRouter()


@metrics_router.get("/metrics")
def get_metrics(response: Response):
    response.headers["Content-Type"] = CONTENT_TYPE_LATEST
    return generate_latest()
