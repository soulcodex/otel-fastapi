from anyio import sleep
from fastapi import APIRouter
from pydantic import BaseModel, Field

example_router = APIRouter()


class SleepRequest(BaseModel):
    sleep_time_seconds: int = Field(gt=0, description="Time to sleep in seconds")


class SleepResponse(BaseModel):
    message: str


@example_router.post(path="/sleep")
async def perform_sleep(req: SleepRequest):
    """Endpoint to simulate sleep for a given number of seconds."""
    await sleep(req.sleep_time_seconds)
    return SleepResponse(message=f"Slept for {req.sleep_time_seconds} seconds")
