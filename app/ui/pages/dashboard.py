from __future__ import annotations

from datetime import datetime

import pandas as pd  # noqa: F401 - Prevents circular import with plotly
import gradio as gr
import plotly.graph_objects as go

from app.config import get_ui_refresh
from app.services.history_service import history_service
from app.services.stats_service import stats_service
from app.state import state
from app.theme import get_theme_colors
from app.ui.components.charts import render_radar_chart


def create_dashboard_tab() -> None:
    gr.Markdown("## 📈 Dashboard")
    gr.Markdown("Overview of your knowledge extraction")

    refresh_interval = get_ui_refresh("dashboard")
    colors = get_theme_colors()

    with gr.Row():
        with gr.Column(scale=2):
            start_btn = gr.Button("▶ Start Auto-Refresh", variant="primary", size="sm")
            stop_btn = gr.Button("⏹ Stop Auto-Refresh", variant="stop", size="sm")
        with gr.Column(scale=1):
            last_updated = gr.HTML(f"<p style='font-size: 12px; color: {colors['text_secondary']};'>Last updated: Never</p>")

    gr.HTML(f"<p style='font-size: 12px; color: {colors['text_secondary']};'>Auto-refreshes every {refresh_interval} seconds</p>")

    gr.HTML("<hr style='margin: 20px 0;'>")

    with gr.Row():
        with gr.Column(scale=3):
            gr.Markdown("### 📊 Extraction Stats")
            stats_plot = gr.Plot()
        with gr.Column(scale=1):
            gr.Markdown("### ⚡ Quick Stats")
            quick_stats = gr.HTML()

    gr.HTML("<hr style='margin: 20px 0;'>")

    gr.Markdown("### 🎯 Method Efficiency (Radar)")
    radar_plot = gr.Plot()

    gr.HTML("<hr style='margin: 20px 0;'>")

    gr.Markdown("### 📝 Recent Activity")
    recent_activity = gr.HTML()

    def update_dashboard() -> dict:
        history_stats = history_service.get_stats()
        method_stats = stats_service.get_method_stats(None)
        colors = get_theme_colors()
        
        radar_fig = render_radar_chart(method_stats)
        
        quick_html = _render_quick_stats(history_stats)
        activity_html = _render_recent_activity()
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        return {
            stats_plot: _render_stats_gauge(history_stats),
            quick_stats: quick_html,
            radar_plot: radar_fig,
            recent_activity: activity_html,
            last_updated: f"<p style='font-size: 12px; color: {colors['text_secondary']};'>Last updated: {timestamp}</p>",
        }

    def start_auto_refresh():
        return gr.Timer(value=refresh_interval, active=True)

    def stop_auto_refresh():
        return gr.Timer(active=False)

    timer = gr.Timer(value=refresh_interval, active=True)
    timer.tick(
        update_dashboard,
        None,
        [stats_plot, quick_stats, radar_plot, recent_activity, last_updated],
    )

    start_btn.click(lambda: None, outputs=[timer])
    stop_btn.click(lambda: None, outputs=[timer])


def _render_quick_stats(history_stats: dict) -> str:
    total_links = history_stats.get("normal_links", 0)
    novels = history_stats.get("novels", 0)
    chapters = history_stats.get("total_chapters", 0)
    words = history_stats.get("total_words", 0)
    
    queue = state.queue
    urls = queue.get("urls", [])
    pending = len([u for u in urls if u.get("status") == "pending"])
    
    colors = get_theme_colors()
    
    return f"""
    <div style='display: flex; flex-direction: column; gap: 15px;'>
        <div style='background: {colors['info_bg']}; padding: 15px; border-radius: 8px; border-left: 4px solid {colors['primary']};'>
            <div style='font-size: 12px; color: {colors['text_secondary']};'>Pending URLs</div>
            <div style='font-size: 28px; font-weight: 600; color: {colors['info']};'>{pending}</div>
        </div>
        <div style='background: {colors['success_bg']}; padding: 15px; border-radius: 8px; border-left: 4px solid {colors['success']};'>
            <div style='font-size: 12px; color: {colors['text_secondary']};'>Total Links</div>
            <div style='font-size: 28px; font-weight: 600; color: {colors['success']};'>{total_links:,}</div>
        </div>
        <div style='background: #fdf2f8; padding: 15px; border-radius: 8px; border-left: 4px solid #ec4899;'>
            <div style='font-size: 12px; color: {colors['text_secondary']};'>Novels</div>
            <div style='font-size: 28px; font-weight: 600; color: #db2777;'>{novels}</div>
        </div>
        <div style='background: {colors['warning_bg']}; padding: 15px; border-radius: 8px; border-left: 4px solid {colors['warning']};'>
            <div style='font-size: 12px; color: {colors['text_secondary']};'>Total Words</div>
            <div style='font-size: 28px; font-weight: 600; color: {colors['warning']};'>{words:,}</div>
        </div>
    </div>
    """


def _render_stats_gauge(history_stats: dict) -> go.Figure:
    total_links = history_stats.get("normal_links", 0)
    novels = history_stats.get("novels", 0)
    chapters = history_stats.get("total_chapters", 0)
    words = history_stats.get("total_words", 0)
    
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="number",
        value=total_links,
        title={"text": "Total Links Extracted"},
        number={"font": {"size": 36}},
        domain={"x": [0, 0.5], "y": [0.6, 1]},
    ))

    fig.add_trace(go.Indicator(
        mode="number",
        value=novels,
        title={"text": "Novels"},
        number={"font": {"size": 28}},
        domain={"x": [0.5, 1], "y": [0.6, 1]},
    ))

    fig.add_trace(go.Indicator(
        mode="number",
        value=chapters,
        title={"text": "Chapters"},
        number={"font": {"size": 28}},
        domain={"x": [0, 0.5], "y": [0, 0.4]},
    ))

    fig.add_trace(go.Indicator(
        mode="number",
        value=words,
        title={"text": "Words Extracted"},
        number={"font": {"size": 28}, "prefix": ""},
        domain={"x": [0.5, 1], "y": [0, 0.4]},
    ))

    fig.update_layout(
        height=280,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    
    return fig


def _render_recent_activity() -> str:
    recent = stats_service.get_recent(10)
    colors = get_theme_colors()
    
    if not recent:
        return f"<p style='color: {colors['text_secondary']};'>No recent activity. Start scraping to see results here.</p>"
    
    html = f"""
    <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
    <thead>
        <tr style='background: {colors['bg_secondary']};'>
            <th style='padding: 8px; text-align: left; font-size: 12px; color: {colors['text_secondary']};'>Status</th>
            <th style='padding: 8px; text-align: left; font-size: 12px; color: {colors['text_secondary']};'>Method</th>
            <th style='padding: 8px; text-align: right; font-size: 12px; color: {colors['text_secondary']};'>Time</th>
            <th style='padding: 8px; text-align: left; font-size: 12px; color: {colors['text_secondary']};'>URL</th>
        </tr>
    </thead>
    <tbody>
    """
    
    for item in recent:
        status_icon = "✅" if item.get("success") else "❌"
        method = item.get("method", "unknown").replace("_", " ").title()
        time_ms = item.get("time_ms", 0)
        domain = item.get("domain", "")
        
        html += f"""
        <tr style='border-bottom: 1px solid {colors['border']};'>
            <td style='padding: 8px;'>{status_icon}</td>
            <td style='padding: 8px; font-size: 12px; color: {colors['text_primary']};'>{method}</td>
            <td style='padding: 8px; text-align: right; font-size: 12px; color: {colors['text_secondary']};'>{time_ms}ms</td>
            <td style='padding: 8px; font-size: 12px; color: {colors['text_secondary']}; max-width: 200px; overflow: hidden; text-overflow: ellipsis;'>{domain}</td>
        </tr>
        """
    
    html += "</tbody></table>"
    return html
