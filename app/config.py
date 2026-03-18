from __future__ import annotations

import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"

_settings_cache = None


def load_settings() -> dict:
    global _settings_cache
    if _settings_cache is None:
        try:
            with open(SETTINGS_FILE) as f:
                _settings_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            _settings_cache = {}
    return _settings_cache


def get_setting(key: str, default=None):
    settings = load_settings()
    return settings.get(key, default)


def get_ui_refresh(tab: str) -> float:
    val = get_setting(f"ui_refresh_{tab}", 3)
    if val is None:
        return 3.0
    return float(val)


def save_settings(settings: dict) -> None:
    global _settings_cache
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)
    _settings_cache = settings


def update_setting(key: str, value) -> None:
    settings = load_settings()
    settings[key] = value
    save_settings(settings)
