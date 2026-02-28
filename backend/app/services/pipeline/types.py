from __future__ import annotations

from typing import Any

from app.db.models import Job, JobStatus


def set_job_state(
    job: Job,
    *,
    status: JobStatus,
    stage: str,
    percent: int,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    history = list(job.progress.get("history", [])) if isinstance(job.progress, dict) else []
    if not history or history[-1] != stage:
        history.append(stage)
    job.status = status
    job.progress = {
        "stage": stage,
        "percent": percent,
        "history": history,
    }
    if result is not None:
        job.result = result
    if error is not None:
        job.error = error
