from __future__ import annotations

from typing import Literal

ThemeMode = Literal["light", "dark"]

THEME_COLORS: dict[ThemeMode, dict[str, str]] = {
    "light": {
        "bg_primary": "#ffffff",
        "bg_secondary": "#f9fafb",
        "bg_tertiary": "#f3f4f6",
        "bg_card": "#ffffff",
        "bg_input": "#ffffff",
        "text_primary": "#111827",
        "text_secondary": "#6b7280",
        "text_muted": "#9ca3af",
        "border": "#e5e7eb",
        "border_focus": "#3b82f6",
        "primary": "#3b82f6",
        "primary_hover": "#2563eb",
        "success": "#16a34a",
        "success_bg": "#dcfce7",
        "warning": "#d97706",
        "warning_bg": "#fef3c7",
        "danger": "#dc2626",
        "danger_bg": "#fee2e2",
        "info": "#1d4ed8",
        "info_bg": "#dbeafe",
    },
    "dark": {
        "bg_primary": "#111827",
        "bg_secondary": "#1f2937",
        "bg_tertiary": "#374151",
        "bg_card": "#1f2937",
        "bg_input": "#374151",
        "text_primary": "#f9fafb",
        "text_secondary": "#9ca3af",
        "text_muted": "#6b7280",
        "border": "#374151",
        "border_focus": "#60a5fa",
        "primary": "#3b82f6",
        "primary_hover": "#60a5fa",
        "success": "#22c55e",
        "success_bg": "#14532d",
        "warning": "#f59e0b",
        "warning_bg": "#78350f",
        "danger": "#ef4444",
        "danger_bg": "#7f1d1d",
        "info": "#3b82f6",
        "info_bg": "#1e3a8a",
    },
}

STATUS_COLORS: dict[str, dict[ThemeMode, dict[str, str]]] = {
    "pending": {
        "light": {"bg": "#dbeafe", "text": "#1d4ed8"},
        "dark": {"bg": "#1e3a8a", "text": "#60a5fa"},
    },
    "completed": {
        "light": {"bg": "#dcfce7", "text": "#16a34a"},
        "dark": {"bg": "#14532d", "text": "#22c55e"},
    },
    "failed": {
        "light": {"bg": "#fee2e2", "text": "#dc2626"},
        "dark": {"bg": "#7f1d1d", "text": "#f87171"},
    },
    "processing": {
        "light": {"bg": "#fef3c7", "text": "#d97706"},
        "dark": {"bg": "#78350f", "text": "#fbbf24"},
    },
}

TYPE_COLORS: dict[str, dict[ThemeMode, dict[str, str]]] = {
    "normal": {
        "light": {"bg": "#e0e7ff", "text": "#4338ca"},
        "dark": {"bg": "#312e81", "text": "#a5b4fc"},
    },
    "novel": {
        "light": {"bg": "#fce7f3", "text": "#be185d"},
        "dark": {"bg": "#831843", "text": "#f9a8d4"},
    },
    "heavy": {
        "light": {"bg": "#fef3c7", "text": "#b45309"},
        "dark": {"bg": "#78350f", "text": "#fdba74"},
    },
    "skip": {
        "light": {"bg": "#f3f4f6", "text": "#6b7280"},
        "dark": {"bg": "#374151", "text": "#9ca3af"},
    },
}


def get_theme_mode() -> ThemeMode:
    try:
        from app.state import state
        return state.get_setting("theme", "light")  # type: ignore[no-any-return]
    except Exception:
        return "light"


def get_theme_colors(theme: ThemeMode | None = None) -> dict[str, str]:
    if theme is None:
        theme = get_theme_mode()
    return THEME_COLORS[theme].copy()


def get_status_colors(status: str, theme: ThemeMode | None = None) -> dict[str, str]:
    if theme is None:
        theme = get_theme_mode()
    return STATUS_COLORS.get(status, STATUS_COLORS["pending"])[theme].copy()


def get_type_colors(type_name: str, theme: ThemeMode | None = None) -> dict[str, str]:
    if theme is None:
        theme = get_theme_mode()
    return TYPE_COLORS.get(type_name, TYPE_COLORS["normal"])[theme].copy()


def generate_css_variables(theme: ThemeMode) -> str:
    colors = THEME_COLORS[theme]
    vars_lines = [f"    --{key}: {value};" for key, value in colors.items()]
    return "\n".join(vars_lines)


def generate_all_css() -> str:
    light_vars = generate_css_variables("light")
    dark_vars = generate_css_variables("dark")
    
    return f"""
:root {{
{light_vars}
}}

[data-theme="dark"] {{
{dark_vars}
}}

@media (prefers-color-scheme: dark) {{
:root {{
{dark_vars}
}}
}}
"""


def card_style(theme: ThemeMode | None = None, **extra) -> str:
    colors = get_theme_colors(theme)
    base = f"background: {colors['bg_card']}; border: 1px solid {colors['border']}; border-radius: 8px; padding: 16px;"
    for key, val in extra.items():
        base += f" {key}: {val};"
    return base


def text_style(theme: ThemeMode | None = None, secondary: bool = False, **extra) -> str:
    colors = get_theme_colors(theme)
    color = colors["text_secondary"] if secondary else colors["text_primary"]
    base = f"color: {color};"
    for key, val in extra.items():
        base += f" {key}: {val};"
    return base


def badge_html(text: str, status: str, theme: ThemeMode | None = None) -> str:
    colors = get_status_colors(status, theme)
    return f"<span style='background: {colors['bg']}; color: {colors['text']}; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 500;'>{text}</span>"


def type_badge_html(text: str, type_name: str, theme: ThemeMode | None = None) -> str:
    colors = get_type_colors(type_name, theme)
    return f"<span style='background: {colors['bg']}; color: {colors['text']}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500;'>{text}</span>"


def stat_card(value: str | int, label: str, color: str = "#3b82f6", theme: ThemeMode | None = None) -> str:
    colors = get_theme_colors(theme)
    return f"""
<div style="text-align: center; padding: 16px; background: {colors['bg_secondary']}; border-radius: 8px;">
    <div style="font-size: 28px; font-weight: 700; color: {color};">{value}</div>
    <div style="font-size: 12px; color: {colors['text_secondary']}; margin-top: 4px;">{label}</div>
</div>
"""


def table_row_style(theme: ThemeMode | None = None, alternate: bool = False) -> str:
    colors = get_theme_colors(theme)
    bg = colors["bg_secondary"] if alternate else colors["bg_primary"]
    return f"background: {bg};"


def input_style(theme: ThemeMode | None = None, **extra) -> str:
    colors = get_theme_colors(theme)
    base = f"background: {colors['bg_input']}; border: 1px solid {colors['border']}; color: {colors['text_primary']}; border-radius: 6px; padding: 8px 12px;"
    for key, val in extra.items():
        base += f" {key}: {val};"
    return base
