from __future__ import annotations

import gradio as gr

from app.config import get_ui_refresh
from app.services.stats_service import stats_service
from app.services.history_service import history_service
from app.theme import get_theme_colors


def create_results_tab() -> None:
    gr.Markdown("## 📄 Scraped Results")

    refresh_interval = get_ui_refresh("results")

    with gr.Row():
        filter_dropdown = gr.Dropdown(
            label="Filter",
            choices=["All", "Success", "Failed"],
            value="All",
            scale=1,
        )
        sort_dropdown = gr.Dropdown(
            label="Sort",
            choices=["Date (Newest)", "Date (Oldest)", "Domain (A-Z)", "Domain (Z-A)", "Words (High)", "Words (Low)", "Time (Fast)", "Time (Slow)"],
            value="Date (Newest)",
            scale=1,
        )
        search_input = gr.Textbox(
            label="Search",
            placeholder="Search by URL or domain...",
            scale=2,
        )
        search_btn = gr.Button("🔍 Search", size="sm")
        refresh_btn = gr.Button("🔄 Refresh", size="sm")

    gr.HTML(f"<p style='font-size: 12px; color: {get_theme_colors()['text_muted']};'>Auto-refreshes every {refresh_interval} seconds</p>")

    gr.HTML("<hr>")

    results_container = gr.HTML(value=render_results("All", "Date (Newest)", ""))

    def update_results(filter_val: str, sort_val: str, search_val: str) -> str:
        return render_results(filter_val, sort_val, search_val)

    search_btn.click(
        update_results,
        inputs=[filter_dropdown, sort_dropdown, search_input],
        outputs=[results_container],
    )

    refresh_btn.click(
        update_results,
        inputs=[filter_dropdown, sort_dropdown, search_input],
        outputs=[results_container],
    )

    timer = gr.Timer(refresh_interval)
    timer.tick(
        lambda: render_results(filter_dropdown.value, sort_dropdown.value, search_input.value),
        None,
        [results_container],
    )


def render_results(filter_val: str = "All", sort_val: str = "Date (Newest)", search_val: str = "") -> str:
    colors = get_theme_colors()
    # Get recent successful scrapes from stats
    recent = stats_service.get_recent(100)

    # Apply filter
    if filter_val == "Success":
        recent = [r for r in recent if r.get("success")]
    elif filter_val == "Failed":
        recent = [r for r in recent if not r.get("success")]

    # Apply search
    if search_val:
        search_lower = search_val.lower()
        recent = [r for r in recent if search_lower in r.get("url", "").lower() or search_lower in r.get("domain", "").lower()]

    # Apply sort
    if sort_val == "Date (Newest)":
        recent = sorted(recent, key=lambda x: x.get("timestamp", ""), reverse=True)
    elif sort_val == "Date (Oldest)":
        recent = sorted(recent, key=lambda x: x.get("timestamp", ""))
    elif sort_val == "Domain (A-Z)":
        recent = sorted(recent, key=lambda x: x.get("domain", ""))
    elif sort_val == "Domain (Z-A)":
        recent = sorted(recent, key=lambda x: x.get("domain", ""), reverse=True)
    elif sort_val == "Words (High)":
        recent = sorted(recent, key=lambda x: x.get("word_count", 0), reverse=True)
    elif sort_val == "Words (Low)":
        recent = sorted(recent, key=lambda x: x.get("word_count", 0))
    elif sort_val == "Time (Fast)":
        recent = sorted(recent, key=lambda x: x.get("time_ms", 0))
    elif sort_val == "Time (Slow)":
        recent = sorted(recent, key=lambda x: x.get("time_ms", 0), reverse=True)

    # Pagination (show first 20)
    page_size = 20
    total_count = len(recent)
    recent = recent[:page_size]

    if not recent:
        return f"""
        <div style="text-align: center; padding: 40px; color: {colors['text_muted']};">
            <p style="font-size: 18px;">No URLs scraped yet.</p>
            <p>Go to Add Links tab to add URLs and start scraping!</p>
        </div>
        """

    # Group by domain
    domains: dict = {}
    for item in recent:
        if not item.get("success"):
            continue
        domain = item.get("domain", "unknown")
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(item)

    # Get history stats
    history_stats = history_service.get_stats()

    html = f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;">
        <div style="background: {colors['info_bg']}; padding: 16px; border-radius: 8px; text-align: center;">
            <div style="font-size: 28px; font-weight: 700; color: {colors['info']};">{history_stats.get('normal_links', 0)}</div>
            <div style="font-size: 12px; color: {colors['text_secondary']};">Normal Links</div>
        </div>
        <div style="background: #fdf2f8; padding: 16px; border-radius: 8px; text-align: center;">
            <div style="font-size: 28px; font-weight: 700; color: #db2777;">{history_stats.get('novels', 0)}</div>
            <div style="font-size: 12px; color: {colors['text_secondary']};">Novels</div>
        </div>
        <div style="background: {colors['success_bg']}; padding: 16px; border-radius: 8px; text-align: center;">
            <div style="font-size: 28px; font-weight: 700; color: {colors['success']};">{history_stats.get('total_chapters', 0)}</div>
            <div style="font-size: 12px; color: {colors['text_secondary']};">Chapters</div>
        </div>
        <div style="background: {colors['warning_bg']}; padding: 16px; border-radius: 8px; text-align: center;">
            <div style="font-size: 28px; font-weight: 700; color: {colors['warning']};">{history_stats.get('total_words', 0):,}</div>
            <div style="font-size: 12px; color: {colors['text_secondary']};">Words</div>
        </div>
    </div>
    """

    html += "<h3>Recently Scraped URLs</h3>"
    border = colors['border']
    html += f"""
    <table style="width: 100%; border-collapse: collapse; margin-top: 12px;">
        <thead>
            <tr style="background: {colors['bg_secondary']};">
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid {border};">Status</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid {border};">Domain</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid {border};">URL</th>
                <th style="padding: 12px; text-align: right; border-bottom: 2px solid {border};">Words</th>
                <th style="padding: 12px; text-align: right; border-bottom: 2px solid {border};">Time</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid {border};">Method</th>
            </tr>
        </thead>
        <tbody>
    """

    for item in recent:
        status_icon = "✅" if item.get("success") else "❌"
        status_color = colors['success'] if item.get("success") else colors['danger']
        
        url = item.get("url", "")
        domain = item.get("domain", "")
        word_count = item.get("word_count", 0)
        time_ms = item.get("time_ms", 0)
        method = item.get("method", "unknown").replace("_", " ").title()
        timestamp = item.get("timestamp", "")[:19] if item.get("timestamp") else ""
        
        display_url = url[:60] + "..." if len(url) > 60 else url

        html += f"""
            <tr style="border-bottom: 1px solid {colors['bg_tertiary']};">
                <td style="padding: 10px;"><span style="color: {status_color};">{status_icon}</span></td>
                <td style="padding: 10px; font-weight: 500;">{domain}</td>
                <td style="padding: 10px; font-size: 12px; color: {colors['text_muted']};" title="{url}">{display_url}</td>
                <td style="padding: 10px; text-align: right;">{word_count:,}</td>
                <td style="padding: 10px; text-align: right; color: {colors['text_muted']};">{time_ms}ms</td>
                <td style="padding: 10px; font-size: 12px;">{method}</td>
            </tr>
        """

    html += "</tbody></table>"

    # Pagination info
    if total_count > page_size:
        html += f"""
        <div style="margin-top: 16px; text-align: center; color: {colors['text_muted']};">
            Showing 1-{len(recent)} of {total_count} results
        </div>
        """

    return html
