from __future__ import annotations

import signal
import sys

import gradio as gr

from app.theme import generate_all_css, get_theme_mode
from app.ui.components.header import render_header
from app.ui.pages.add_links import create_add_links_tab
from app.ui.pages.analytics import create_analytics_tab
from app.ui.pages.dashboard import create_dashboard_tab
from app.ui.pages.notifications import create_notifications_tab
from app.ui.pages.queue import create_queue_tab
from app.ui.pages.results import create_results_tab
from app.ui.pages.scheduler import create_scheduler_tab
from app.ui.pages.settings import create_settings_tab


def get_css() -> str:
    theme_vars = generate_all_css()
    
    return f"""/* Theme Variables - Auto-generated */
{theme_vars}

/* Base Theme Colors */
:root {{
    --primary: #3b82f6;
    --primary-hover: #2563eb;
    --success: #22c55e;
    --warning: #f59e0b;
    --danger: #ef4444;
    --accent-blue: #2563eb;
    --accent-pink: #db2777;
    --accent-green: #16a34a;
    --accent-amber: #d97706;
}}

/* Header Styling */
.header-row {{
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    padding: 20px;
    margin: -20px -20px 20px -20px;
    border-radius: 0;
}}

.main-title {{
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    margin: 0 !important;
}}

/* Card Styling */
.card {{
    background: var(--bg-card);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    margin-bottom: 16px;
}}

.card-dark {{
    background: var(--bg-card-dark);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    margin-bottom: 16px;
}}

/* Status Badges - Theme Aware */
.status-badge {{
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    display: inline-block;
}}

.status-badge.pending {{
    background: var(--info-bg);
    color: var(--info);
}}

.status-badge.completed {{
    background: var(--success-bg);
    color: var(--success);
}}

.status-badge.failed {{
    background: var(--danger-bg);
    color: var(--danger);
}}

.status-badge.processing {{
    background: var(--warning-bg);
    color: var(--warning);
}}

/* Type Badges - Theme Aware */
.type-badge {{
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
}}

.type-badge.normal {{
    background: #e0e7ff;
    color: #4338ca;
}}

.type-badge.novel {{
    background: #fce7f3;
    color: #be185d;
}}

.type-badge.heavy {{
    background: #fef3c7;
    color: #b45309;
}}

.type-badge.skip {{
    background: var(--bg-tertiary);
    color: var(--text-secondary);
}}

/* URL Card Styling */
.url-card {{
    background: var(--bg-card);
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    border-left: 4px solid #3b82f6;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    transition: transform 0.2s, box-shadow 0.2s;
}}

.url-card:hover {{
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}}

.url-card.pending {{ border-left-color: #3b82f6; }}
.url-card.completed {{ border-left-color: #22c55e; }}
.url-card.failed {{ border-left-color: #ef4444; }}
.url-card.processing {{ border-left-color: #f59e0b; }}

/* Section Headers */
.section-header {{
    font-size: 20px !important;
    font-weight: 600 !important;
    margin-bottom: 16px !important;
    color: var(--text-primary) !important;
}}

/* Tab Styling */
.tabs {{
    font-weight: 500;
}}

/* Button Enhancements */
button.primary {{
    background: var(--primary) !important;
    transition: background 0.2s;
}}

button.primary:hover {{
    background: var(--primary-hover) !important;
}}

/* Metric Card */
.metric-card {{
    text-align: center;
    padding: 16px;
    background: var(--bg-secondary);
    border-radius: 8px;
}}

.metric-value {{
    font-size: 32px;
    font-weight: 700;
    color: var(--primary);
}}

.metric-label {{
    font-size: 14px;
    color: var(--text-secondary);
    margin-top: 4px;
}}

/* Table Styling */
table {{
    width: 100%;
    border-collapse: collapse;
}}

th {{
    background: var(--bg-secondary);
    padding: 12px;
    text-align: left;
    font-weight: 600;
    font-size: 13px;
    color: var(--text-secondary);
    border-bottom: 2px solid var(--border);
}}

td {{
    padding: 12px;
    border-bottom: 1px solid var(--border);
    font-size: 14px;
    color: var(--text-primary);
}}

tr:hover {{
    background: var(--bg-secondary);
}}

/* Progress Bar */
.progress-bar {{
    height: 8px;
    background: var(--border);
    border-radius: 4px;
    overflow: hidden;
}}

.progress-fill {{
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
}}

/* HR styling */
hr {{
    border: none;
    border-top: 1px solid var(--border);
    margin: 24px 0;
}}

/* Text colors for HTML components - Theme Aware */
.text-primary {{ color: var(--text-primary); }}
.text-secondary {{ color: var(--text-secondary); }}
.text-muted {{ color: var(--text-muted); }}
.bg-card {{ background: var(--bg-card); }}
.bg-secondary {{ background: var(--bg-secondary); }}
.border-default {{ border: 1px solid var(--border); }}
"""

_gradio_app: gr.Blocks | None = None


def create_app() -> gr.Blocks:
    with gr.Blocks(title="KnowledgeAgent") as app:
        render_header()

        with gr.Tab("📊 Dashboard"):
            create_dashboard_tab()

        with gr.Tab("➕ Add Links"):
            create_add_links_tab()

        with gr.Tab("📋 Queue"):
            create_queue_tab()

        with gr.Tab("📄 Results"):
            create_results_tab()

        with gr.Tab("📈 Analytics"):
            create_analytics_tab()

        with gr.Tab("⏰ Scheduler"):
            create_scheduler_tab()

        with gr.Tab("🔔 Notifications"):
            create_notifications_tab()

        with gr.Tab("⚙️ Settings"):
            create_settings_tab()

    return app  # type: ignore[no-any-return]


def _signal_handler(sig, frame) -> None:
    print("\nShutting down gracefully...")
    if _gradio_app is not None:
        _gradio_app.close()
    sys.exit(0)


def main() -> None:
    global _gradio_app

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    _gradio_app = create_app()
    _gradio_app.queue()
    _gradio_app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="violet", radius_size="md"),
        css=get_css(),
    )


if __name__ == "__main__":
    main()
