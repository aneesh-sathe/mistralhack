from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.artifacts import router as artifacts_router
from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as documents_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.modules import router as modules_router
from app.core.settings import get_settings
from app.logging import configure_logging
from app.services.storage import LocalStorage

configure_logging()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.config.app.name)

    origins = {
        settings.config.app.frontend_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    }

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(documents_router)
    app.include_router(modules_router)
    app.include_router(jobs_router)
    app.include_router(artifacts_router)

    @app.on_event("startup")
    def _startup() -> None:
        LocalStorage().ensure_dirs()

    @app.get("/")
    def health() -> dict:
        return {"status": "ok", "service": settings.config.app.name}

    return app


app = create_app()
