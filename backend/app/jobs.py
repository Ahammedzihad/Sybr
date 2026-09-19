"""
Background Job Progress Manager for Batch Uploads.
Tracks processing state for POST /upload and GET /jobs/{id}.
"""
import uuid
from typing import Dict, Optional
from datetime import datetime, timezone
from app.schemas import JobProgressResponse

_JOBS: Dict[str, JobProgressResponse] = {}


def create_job(total: int) -> str:
    """Creates a new tracking job and returns its unique ID."""
    job_id = str(uuid.uuid4())
    now_str = datetime.now(timezone.utc).isoformat()
    _JOBS[job_id] = JobProgressResponse(
        job_id=job_id,
        status="processing",
        total=total,
        processed=0,
        errors=0,
        created_at=now_str,
    )
    return job_id


def update_job_progress(job_id: str, processed_inc: int = 1, error: bool = False) -> None:
    """Increments the processed/error count of an active job."""
    job = _JOBS.get(job_id)
    if not job:
        return

    job.processed += processed_inc
    if error:
        job.errors += 1

    if job.processed >= job.total:
        job.status = "completed" if job.errors < job.total else "failed"
        job.completed_at = datetime.now(timezone.utc).isoformat()


def get_job_status(job_id: str) -> Optional[JobProgressResponse]:
    """Retrieves progress for a specific job."""
    return _JOBS.get(job_id)
