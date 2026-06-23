"""Server-Sent Events streaming endpoint.

Streams evaluation progress as typed SSE events:
  event: progress  → stage + message
  event: rubric    → dimension score breakdown
  event: skills_update → updated skills matrix
  event: complete  → final results
  event: error     → failure details
"""
import asyncio
import json
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

router = APIRouter(tags=["stream"])


async def event_generator(job_id: str):
    """Generate SSE events for an evaluation job.

    In production this subscribes to Redis pub/sub channels
    and forwards events from the BullMQ worker.
    """
    yield {
        "event": "progress",
        "data": json.dumps({
            "stage": "initializing",
            "message": f"Evaluation started for job {job_id}",
            "timestamp": "",
        }),
    }

    await asyncio.sleep(1)

    yield {
        "event": "progress",
        "data": json.dumps({
            "stage": "sandbox_exec",
            "message": "Running code in gVisor sandbox...",
            "timestamp": "",
        }),
    }

    await asyncio.sleep(1)

    yield {
        "event": "rubric",
        "data": json.dumps({
            "dimension": "async_flows",
            "score": 85,
            "maxScore": 100,
            "feedback": "Proper async patterns detected",
        }),
    }

    yield {
        "event": "skills_update",
        "data": json.dumps({
            "skillsMatrix": {"async_flows": 85, "connection_pooling": 72},
        }),
    }

    yield {
        "event": "complete",
        "data": json.dumps({
            "finalScore": 78,
            "nextAction": "keep_level",
            "message": "Evaluation complete.",
        }),
    }


@router.get("/stream/{job_id}")
async def stream_evaluation(job_id: str):
    """Stream evaluation progress as Server-Sent Events."""
    return EventSourceResponse(event_generator(job_id))
