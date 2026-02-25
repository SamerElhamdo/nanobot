"""Admin API routes for config, workspace files, skills, env."""

import json
import os
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from nanobot.config.loader import get_config_path, load_config, save_config
from nanobot.config.schema import Config
from nanobot.web.auth import require_admin_token

# Allowed workspace bootstrap filenames (no path traversal)
BOOTSTRAP_ALLOWED = frozenset({
    "AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md", "IDENTITY.md", "HEARTBEAT.md",
})
# Skill name: alphanumeric, underscore, hyphen only
SKILL_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/health")
def health() -> dict:
    """Public health check. Returns whether admin token is configured."""
    from nanobot.web.auth import is_admin_configured
    return {"status": "ok", "admin_configured": is_admin_configured()}


def _get_workspace_path() -> Path:
    config = load_config()
    return config.workspace_path


# --- Config ---


@router.get("/config", dependencies=[Depends(require_admin_token)])
def get_config() -> dict:
    """Return current config as JSON (for editing)."""
    path = get_config_path()
    if not path.exists():
        return Config().model_dump(by_alias=True)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@router.patch("/config", dependencies=[Depends(require_admin_token)])
def patch_config(body: dict) -> dict:
    """Update config with given JSON (full config). Validates and saves."""
    from nanobot.config.loader import _migrate_config
    data = _migrate_config(dict(body))
    config = Config.model_validate(data)
    save_config(config)
    return config.model_dump(by_alias=True)


# --- Auth check (for login) ---


@router.post("/auth")
def auth_check(body: dict) -> dict:
    """Verify token. Body: { \"token\": \"...\" }. Returns { \"ok\": true } if valid."""
    token_from_body = (body or {}).get("token")
    if not token_from_body:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    expected = os.environ.get("GATEWAY_ADMIN_TOKEN") or os.environ.get("NANOBOT_ADMIN_TOKEN")
    if not (expected or "").strip():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Admin not configured")
    import hmac
    if not hmac.compare_digest((token_from_body or "").strip(), (expected or "").strip()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return {"ok": True}


# --- Workspace files ---


@router.get("/workspace/files", dependencies=[Depends(require_admin_token)])
def list_workspace_files() -> list[dict]:
    """List bootstrap files present in workspace."""
    workspace = _get_workspace_path()
    result = []
    for name in sorted(BOOTSTRAP_ALLOWED):
        path = workspace / name
        result.append({"name": name, "exists": path.exists()})
    return result


@router.get("/workspace/files/{filename}", dependencies=[Depends(require_admin_token)])
def get_workspace_file(filename: str) -> dict:
    """Read one workspace bootstrap file."""
    if filename not in BOOTSTRAP_ALLOWED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")
    path = _get_workspace_path() / filename
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return {"name": filename, "content": path.read_text(encoding="utf-8")}


@router.put("/workspace/files/{filename}", dependencies=[Depends(require_admin_token)])
def put_workspace_file(filename: str, body: dict) -> dict:
    """Write one workspace bootstrap file. Body: { \"content\": \"...\" }."""
    if filename not in BOOTSTRAP_ALLOWED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")
    content = body.get("content")
    if content is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing content")
    path = _get_workspace_path() / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if isinstance(content, str) else str(content), encoding="utf-8")
    return {"name": filename, "ok": True}


# --- Skills ---


@router.get("/skills", dependencies=[Depends(require_admin_token)])
def list_skills() -> list[dict]:
    """List skills (workspace + builtin)."""
    workspace = _get_workspace_path()
    from nanobot.agent.skills import SkillsLoader
    loader = SkillsLoader(workspace)
    return loader.list_skills(filter_unavailable=False)


@router.get("/skills/{name}", dependencies=[Depends(require_admin_token)])
def get_skill(name: str) -> dict:
    """Get skill content by name. Only workspace skills are editable."""
    if not SKILL_NAME_RE.match(name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid skill name")
    workspace = _get_workspace_path()
    from nanobot.agent.skills import SkillsLoader
    loader = SkillsLoader(workspace)
    content = loader.load_skill(name)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    source = "workspace" if (workspace / "skills" / name / "SKILL.md").exists() else "builtin"
    return {"name": name, "content": content, "source": source}


@router.put("/skills/{name}", dependencies=[Depends(require_admin_token)])
def put_skill(name: str, body: dict) -> dict:
    """Write workspace skill SKILL.md. Body: { \"content\": \"...\" }."""
    if not SKILL_NAME_RE.match(name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid skill name")
    content = body.get("content")
    if content is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing content")
    skill_dir = _get_workspace_path() / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        content if isinstance(content, str) else str(content),
        encoding="utf-8",
    )
    return {"name": name, "ok": True}


# --- Env (read-only) ---


@router.get("/env", dependencies=[Depends(require_admin_token)])
def get_env_vars() -> list[dict]:
    """List env var names used by nanobot (values masked). Read-only."""
    from nanobot.providers.registry import PROVIDERS
    extra_keys = [
        "NANOBOT_DEFAULT_MODEL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_ENABLED",
        "TELEGRAM_ALLOW_FROM",
        "TELEGRAM_REPLY_TO_MESSAGE",
    ]
    result = []
    seen = set()
    for spec in PROVIDERS:
        if spec.env_key and spec.env_key not in seen:
            seen.add(spec.env_key)
            val = os.environ.get(spec.env_key)
            result.append({
                "key": spec.env_key,
                "set": bool(val),
                "masked": "***" if val else "",
            })
    for key in extra_keys:
        if key not in seen:
            val = os.environ.get(key)
            result.append({"key": key, "set": bool(val), "masked": "***" if val else ""})
    return sorted(result, key=lambda x: x["key"])
