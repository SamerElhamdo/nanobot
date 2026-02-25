"""FastAPI application for admin UI and API."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from nanobot.web.routes import router as admin_router


def create_app(static_dir: Path | None = None) -> FastAPI:
    """Create FastAPI app with admin API and optional static SPA."""
    app = FastAPI(
        title="Nanobot Admin",
        description="Admin API and UI for nanobot gateway",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(admin_router)

    if static_dir is not None and static_dir.is_dir():
        dist = static_dir / "dist"
        index = dist / "index.html"
        if index.exists():
            app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

            @app.get("/")
            @app.get("/admin")
            @app.get("/admin/")
            def serve_spa():
                return FileResponse(index)

            @app.get("/admin/{path:path}")
            def serve_spa_path(path: str):
                return FileResponse(index)

    return app
