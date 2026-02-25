"""Configuration loading utilities."""

import json
import os
from pathlib import Path

from nanobot.config.schema import Config, ProviderConfig


def get_config_path() -> Path:
    """Get the default configuration file path."""
    return Path.home() / ".nanobot" / "config.json"


def get_data_dir() -> Path:
    """Get the nanobot data directory."""
    from nanobot.utils.helpers import get_data_path
    return get_data_path()


def load_config(config_path: Path | None = None) -> Config:
    """
    Load configuration from file or create default.

    Args:
        config_path: Optional path to config file. Uses default if not provided.

    Returns:
        Loaded configuration object.
    """
    path = config_path or get_config_path()

    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            data = _migrate_config(data)
            config = Config.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Failed to load config from {path}: {e}")
            print("Using default configuration.")
            config = Config()
    else:
        config = Config()

    _apply_provider_env_overlay(config)
    return config


def save_config(config: Config, config_path: Path | None = None) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration to save.
        config_path: Optional path to save to. Uses default if not provided.
    """
    path = config_path or get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump(by_alias=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _apply_provider_env_overlay(config: Config) -> None:
    """
    If a provider's api_key is empty in config, set it from the provider's
    env var (e.g. OPENROUTER_API_KEY). Allows passing API keys via environment
    (e.g. docker-compose environment) without editing config.json.
    """
    from nanobot.providers.registry import PROVIDERS

    for spec in PROVIDERS:
        if not spec.env_key or spec.is_oauth:
            continue
        p = getattr(config.providers, spec.name, None)
        if p is None:
            continue
        env_val = os.environ.get(spec.env_key, "").strip()
        if not p.api_key and env_val:
            setattr(
                config.providers,
                spec.name,
                ProviderConfig(
                    api_key=env_val,
                    api_base=p.api_base,
                    extra_headers=p.extra_headers,
                ),
            )


def _migrate_config(data: dict) -> dict:
    """Migrate old config formats to current."""
    # Move tools.exec.restrictToWorkspace → tools.restrictToWorkspace
    tools = data.get("tools", {})
    exec_cfg = tools.get("exec", {})
    if "restrictToWorkspace" in exec_cfg and "restrictToWorkspace" not in tools:
        tools["restrictToWorkspace"] = exec_cfg.pop("restrictToWorkspace")
    return data
