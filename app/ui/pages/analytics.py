from __future__ import annotations

import gradio as gr

from app.config import get_ui_refresh
from app.services.stats_service import stats_service
from app.theme import get_theme_colors
from app.ui.components.charts import (
    render_daily_line_chart,
    render_efficiency_bar,
    render_method_bar_chart,
    render_radar_chart,
    render_success_pie,
)


TIME_PERIODS = [
    ("All Time", None),
    ("Last 7 days", 7),
    ("Last 15 days", 15),
    ("Last 30 days", 30),
    ("Last 90 days", 90),
]


def create_analytics_tab() -> None:
    gr.Markdown("## 📊 Analytics")
    gr.Markdown("Scraping method performance and trends")

    refresh_interval = get_ui_refresh("analytics")

    with gr.Row():
        period_dropdown = gr.Dropdown(
            label="Time Period",
            choices=[p[0] for p in TIME_PERIODS],
            value="All Time",
            scale=2,
        )
        with gr.Column(scale=1):
            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh", size="sm")
            gr.HTML(f"<p style='font-size: 12px; color: {get_theme_colors()['text_muted']};'>Auto-refreshes every {refresh_interval} seconds</p>")

    gr.HTML("<hr style='margin: 20px 0;'>")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Overview")
            summary_plot = gr.Plot()
        with gr.Column(scale=2):
            gr.Markdown("### Method Performance")
            radar_plot = gr.Plot()

    gr.HTML("<hr style='margin: 20px 0;'>")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Success vs Failed")
            pie_plot = gr.Plot()
        with gr.Column(scale=2):
            gr.Markdown("### Success/Fail by Method")
            bar_plot = gr.Plot()

    gr.HTML("<hr style='margin: 20px 0;'>")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Efficiency Scores")
            eff_plot = gr.Plot()
        with gr.Column(scale=2):
            gr.Markdown("### Daily Activity")
            line_plot = gr.Plot()

    gr.HTML("<hr style='margin: 20px 0;'>")

    with gr.Row():
        gr.Markdown("### 📋 Method Details")
    
    method_details = gr.HTML()

    def update_charts(period_name: str) -> dict:
        days = next((p[1] for p in TIME_PERIODS if p[0] == period_name), None)
        
        method_stats = stats_service.get_method_stats(days)
        summary = stats_service.get_summary_stats(days)
        daily = stats_service.get_daily_activity(days or 14)
        
        return {
            summary_plot: render_success_pie(summary),
            radar_plot: render_radar_chart(method_stats),
            pie_plot: render_success_pie(summary),
            bar_plot: render_method_bar_chart(method_stats),
            eff_plot: render_efficiency_bar(method_stats),
            line_plot: render_daily_line_chart(daily),
            method_details: _render_method_details(method_stats),
        }

    refresh_btn.click(
        update_charts,
        inputs=[period_dropdown],
        outputs=[summary_plot, radar_plot, pie_plot, bar_plot, eff_plot, line_plot, method_details],
    )
    period_dropdown.change(
        update_charts,
        inputs=[period_dropdown],
        outputs=[summary_plot, radar_plot, pie_plot, bar_plot, eff_plot, line_plot, method_details],
    )

    timer = gr.Timer(refresh_interval)
    timer.tick(
        update_charts,
        inputs=[period_dropdown],
        outputs=[summary_plot, radar_plot, pie_plot, bar_plot, eff_plot, line_plot, method_details],
    )


def _render_method_details(method_stats: dict) -> str:
    colors = get_theme_colors()
    if not method_stats:
        return "<p>No method data available</p>"
    
    border = colors['border']
    html = f"""
    <table style='width:100%; border-collapse: collapse; margin-top: 10px;'>
    <thead>
        <tr style='background: {colors['bg_tertiary']};'>
            <th style='padding: 10px; text-align: left; border: 1px solid {border};'>Method</th>
            <th style='padding: 10px; text-align: right; border: 1px solid {border};'>Attempts</th>
            <th style='padding: 10px; text-align: right; border: 1px solid {border};'>Success</th>
            <th style='padding: 10px; text-align: right; border: 1px solid {border};'>Failed</th>
            <th style='padding: 10px; text-align: right; border: 1px solid {border};'>Success Rate</th>
            <th style='padding: 10px; text-align: right; border: 1px solid {border};'>Avg Time</th>
            <th style='padding: 10px; text-align: right; border: 1px solid {border};'>Efficiency</th>
        </tr>
    </thead>
    <tbody>
    """
    
    for method, data in sorted(method_stats.items(), key=lambda x: x[1].get("total_attempts", 0), reverse=True):
        sr = data.get("success_rate", 0)
        sr_color = colors['success'] if sr >= 70 else colors['warning'] if sr >= 40 else colors['danger']
        
        html += f"""
        <tr>
            <td style='padding: 10px; border: 1px solid {border};'>{method.replace('_', ' ').title()}</td>
            <td style='padding: 10px; text-align: right; border: 1px solid {border};'>{data.get('total_attempts', 0)}</td>
            <td style='padding: 10px; text-align: right; border: 1px solid {border}; color: {colors['success']};'>{data.get('success', 0)}</td>
            <td style='padding: 10px; text-align: right; border: 1px solid {border}; color: {colors['danger']};'>{data.get('failed', 0)}</td>
            <td style='padding: 10px; text-align: right; border: 1px solid {border}; color: {sr_color}; font-weight: 600;'>{sr:.1f}%</td>
            <td style='padding: 10px; text-align: right; border: 1px solid {border};'>{data.get('avg_time_ms', 0)}ms</td>
            <td style='padding: 10px; text-align: right; border: 1px solid {border}; font-weight: 600;'>{data.get('efficiency_score', 0):.1f}</td>
        </tr>
        """
    
    html += "</tbody></table>"
    return html
