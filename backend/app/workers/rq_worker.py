from __future__ import annotations

from redis import Redis
from rq import Queue, Worker

from app.core.settings import get_settings

# Ensure worker imports job modules so functions are discoverable.
from app.services.pipeline import generate_module_assets_job  # noqa: F401
from app.services.pipeline import parse_document_job  # noqa: F401


def main() -> None:
    settings = get_settings()
    redis_conn = Redis.from_url(settings.redis_url)
    queue = Queue("default", connection=redis_conn)
    worker = Worker([queue], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
