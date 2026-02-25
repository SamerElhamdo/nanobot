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


# Env vars for optional config merge (Docker / first-run)
_ENV_DEFAULT_MODEL = "NANOBOT_DEFAULT_MODEL"
_ENV_TELEGRAM_TOKEN = "TELEGRAM_BOT_TOKEN"
_ENV_TELEGRAM_ENABLED = "TELEGRAM_ENABLED"
_ENV_TELEGRAM_ALLOW_FROM = "TELEGRAM_ALLOW_FROM"  # Comma-separated: user1,123456
_ENV_TELEGRAM_REPLY_TO_MESSAGE = "TELEGRAM_REPLY_TO_MESSAGE"  # 1, true, yes

_DEFAULT_MODEL_SCHEMA = "anthropic/claude-opus-4-5"


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


def merge_env_into_config(config: Config, only_if_empty: bool = True) -> None:
    """
    Merge env vars into config: default model, Telegram token/enabled.
    Used at first-run or by ensure-config so Docker can set values via env.

    When only_if_empty=True, only set a field if it is empty (or model is
    still the schema default), so existing user values are preserved.
    When only_if_empty=False, set from env when provided (for new config).
    """
    from nanobot.config.schema import TelegramConfig

    # Default model
    env_model = os.environ.get(_ENV_DEFAULT_MODEL, "").strip()
    if env_model:
        if not only_if_empty:
            config.agents.defaults.model = env_model
        elif config.agents.defaults.model == _DEFAULT_MODEL_SCHEMA or not config.agents.defaults.model:
            config.agents.defaults.model = env_model

    # Telegram: token, enabled, allow_from, reply_to_message from env
    env_token = os.environ.get(_ENV_TELEGRAM_TOKEN, "").strip()
    env_enabled = os.environ.get(_ENV_TELEGRAM_ENABLED, "").strip().lower() in ("1", "true", "yes")
    env_allow_from_raw = os.environ.get(_ENV_TELEGRAM_ALLOW_FROM, "").strip()
    env_allow_from = [x.strip() for x in env_allow_from_raw.split(",") if x.strip()] if env_allow_from_raw else []
    env_reply = os.environ.get(_ENV_TELEGRAM_REPLY_TO_MESSAGE, "").strip().lower() in ("1", "true", "yes")
    tg = config.channels.telegram
    set_token = bool(env_token and (not only_if_empty or not tg.token))
    has_token = bool(env_token or tg.token)
    set_enabled = bool(
        env_enabled and has_token and (not only_if_empty or not tg.enabled)
    )
    set_allow_from = bool(env_allow_from and (not only_if_empty or not tg.allow_from))
    set_reply = bool(env_reply and (not only_if_empty or not tg.reply_to_message))
    if set_token or set_enabled or set_allow_from or set_reply:
        new_token = env_token if set_token else tg.token
        new_enabled = True if set_enabled else tg.enabled
        new_allow_from = env_allow_from if set_allow_from else tg.allow_from
        new_reply = True if set_reply else tg.reply_to_message
        config.channels.telegram = TelegramConfig(
            enabled=new_enabled,
            token=new_token,
            allow_from=new_allow_from,
            proxy=tg.proxy,
            reply_to_message=new_reply,
        )


def ensure_config(config_path: Path | None = None) -> Config:
    """
    Ensure config file exists and is updated from env without overwriting
    existing values. Use at container startup before starting the gateway.

    - If no file: create default, apply provider overlay + env merge, save.
    - If file exists: load, apply provider overlay + env merge (only empty
      fields), save. Preserves all existing non-empty values.
    """
    path = config_path or get_config_path()
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            data = _migrate_config(data)
            config = Config.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            config = Config()
            _apply_provider_env_overlay(config)
            merge_env_into_config(config, only_if_empty=False)
        else:
            _apply_provider_env_overlay(config)
            merge_env_into_config(config, only_if_empty=True)
    else:
        config = Config()
        _apply_provider_env_overlay(config)
        merge_env_into_config(config, only_if_empty=False)

    save_config(config, config_path)
    return config


def _migrate_config(data: dict) -> dict:
    """Migrate old config formats to current."""
    # Move tools.exec.restrictToWorkspace → tools.restrictToWorkspace
    tools = data.get("tools", {})
    exec_cfg = tools.get("exec", {})
    if "restrictToWorkspace" in exec_cfg and "restrictToWorkspace" not in tools:
        tools["restrictToWorkspace"] = exec_cfg.pop("restrictToWorkspace")
    return data
