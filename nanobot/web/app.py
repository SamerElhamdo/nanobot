"""FastAPI app for admin API: config, workspace, health. Token auth via GATEWAY_ADMIN_TOKEN."""

import os
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Request, Body

from nanobot.config.loader import load_config, save_config, get_config_path
from nanobot.config.schema import Config


def _admin_token() -> str:
    return (os.environ.get("GATEWAY_ADMIN_TOKEN") or "").strip()


async def require_admin(request: Request) -> None:
    """Dependency: require Authorization Bearer token if GATEWAY_ADMIN_TOKEN is set."""
    token = _admin_token()
    if not token:
        return  # No token configured → allow (caller can restrict in production)
    auth = request.headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    if auth[7:].strip() != token:
        raise HTTPException(status_code=401, detail="Invalid token")


def create_app(config_path: Path | None = None, workspace_path: Path | None = None) -> FastAPI:
    """Create FastAPI app with config and workspace paths (for gateway)."""
    config_path = config_path or get_config_path()
    workspace_path = workspace_path or (load_config(config_path).workspace_path if config_path.exists() else Path.home() / ".nanobot" / "workspace")

    app = FastAPI(title="Nanobot Admin API", version="0.1")

    @app.get("/api/admin/health")
    async def health():
        return {"ok": True}

    @app.get("/api/admin/config", dependencies=[Depends(require_admin)])
    async def get_config_route():
        try:
            cfg = load_config(config_path)
            return cfg.model_dump(by_alias=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/api/admin/config", dependencies=[Depends(require_admin)])
    async def put_config_route(body: dict):
        try:
            cfg = Config.model_validate(body)
            save_config(cfg, config_path)
            return {"ok": True}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/admin/env", dependencies=[Depends(require_admin)])
    async def get_env():
        """Return env var names that affect config (no secret values)."""
        keys = [
            "OPENROUTER_API_KEY", "NANOBOT_DEFAULT_MODEL",
            "TELEGRAM_BOT_TOKEN", "TELEGRAM_ENABLED", "TELEGRAM_ALLOW_FROM", "TELEGRAM_REPLY_TO_MESSAGE",
            "GATEWAY_ADMIN_TOKEN",
        ]
        return {k: "set" if os.environ.get(k) else "unset" for k in keys}

    @app.get("/api/admin/skills", dependencies=[Depends(require_admin)])
    async def list_skills():
        from nanobot.utils.helpers import get_data_path
        skills_dir = get_data_path() / "skills"
        if not skills_dir.exists():
            return {"paths": [], "files": []}
        paths = []
        for f in sorted(skills_dir.iterdir()):
            if f.suffix in (".md", ".sh") and not f.name.startswith("."):
                paths.append(f.name)
        return {"paths": paths, "files": paths}

    @app.get("/api/admin/workspace/files", dependencies=[Depends(require_admin)])
    async def list_workspace_files():
        if not workspace_path.exists():
            return {"paths": []}
        names = []
        for f in sorted(workspace_path.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                names.append(f.name)
        return {"paths": names}

    @app.get("/api/admin/workspace/files/{name:path}", dependencies=[Depends(require_admin)])
    async def get_workspace_file(name: str):
        path = (workspace_path / name).resolve()
        if not path.is_relative_to(workspace_path.resolve()) or not path.exists() or not path.is_file():
            raise HTTPException(status_code=404, detail="Not found")
        return {"content": path.read_text(encoding="utf-8", errors="replace")}

    @app.put("/api/admin/workspace/files/{name:path}", dependencies=[Depends(require_admin)])
    async def put_workspace_file(name: str, body: dict = Body(...)):
        content = body.get("content", "")
        path = (workspace_path / name).resolve()
        if not path.is_relative_to(workspace_path.resolve()):
            raise HTTPException(status_code=400, detail="Invalid path")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"ok": True}

    return app
