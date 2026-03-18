from __future__ import annotations

import gradio as gr

from app.config import get_ui_refresh
from app.services.queue_service import queue_service
from app.theme import get_theme_colors


def create_queue_tab() -> None:
    gr.Markdown("## 📋 Queue Management")

    refresh_interval = get_ui_refresh("queue")
    colors = get_theme_colors()

    with gr.Row():
        start_btn = gr.Button("▶ Start Auto-Refresh", variant="primary", size="sm")
        stop_btn = gr.Button("⏹ Stop Auto-Refresh", variant="stop", size="sm")
        refresh_btn = gr.Button("🔄 Refresh Now", size="sm")
        clear_done_btn = gr.Button("🗑️ Clear Completed", size="sm")

    gr.HTML(f"<p style='font-size: 12px; color: {colors['text_secondary']};'>Auto-refreshes every {refresh_interval} seconds</p>")

    with gr.Tab("Pending URLs"):
        pending_container = gr.HTML()

    with gr.Tab("Pending Novels"):
        novels_container = gr.HTML()

    with gr.Tab("Retry (Normal)"):
        retry_normal_container = gr.HTML()

    with gr.Tab("Retry (Novel)"):
        retry_novel_container = gr.HTML()

    def update_all() -> dict:
        return {
            pending_container: render_pending_urls_html(),
            novels_container: render_pending_novels_html(),
            retry_normal_container: render_retry_normal_html(),
            retry_novel_container: render_retry_novel_html(),
        }

    refresh_btn.click(update_all, outputs=[pending_container, novels_container, retry_normal_container, retry_novel_container])
    clear_done_btn.click(clear_completed, outputs=[pending_container])

    timer = gr.Timer(value=refresh_interval, active=True)
    timer.tick(update_all, None, [pending_container, novels_container, retry_normal_container, retry_novel_container])

    update_all()


def clear_completed() -> str:
    queue_service.clear_completed()
    return render_pending_urls_html()


def render_pending_urls_html() -> str:
    colors = get_theme_colors()
    all_urls = queue_service.get_all_urls()

    urls = [u for u in all_urls if u.status == "pending"]
    completed = [u for u in all_urls if u.status == "completed"]
    failed = [u for u in all_urls if u.status == "failed"]

    stats_html = f"""
    <div style="display: flex; gap: 20px; margin-bottom: 20px;">
        <div style="background: {colors['info_bg']}; padding: 10px 20px; border-radius: 8px;">
            <strong style="color: {colors['info']};">Pending:</strong> {len(urls)}
        </div>
        <div style="background: {colors['success_bg']}; padding: 10px 20px; border-radius: 8px;">
            <strong style="color: {colors['success']};">Completed:</strong> {len(completed)}
        </div>
        <div style="background: {colors['danger_bg']}; padding: 10px 20px; border-radius: 8px;">
            <strong style="color: {colors['danger']};">Failed:</strong> {len(failed)}
        </div>
    </div>
    """

    if not urls:
        return stats_html + f"<p style='color: {colors['text_secondary']};'>No pending URLs</p>"

    html = stats_html + f"<h3 style='color: {colors['text_primary']};'>Pending URLs (" + str(len(urls)) + ")</h3><table style='width:100%;'>"
    html += f"<tr><th style='color: {colors['text_secondary']};'>Select</th><th style='color: {colors['text_secondary']};'>URL</th><th style='color: {colors['text_secondary']};'>Type</th><th style='color: {colors['text_secondary']};'>Tags</th><th style='color: {colors['text_secondary']};'>Actions</th></tr>"

    for idx, entry in enumerate(urls):
        url = entry.url
        route = entry.type
        tags = ", ".join(entry.tags[:3]) if entry.tags else "-"

        html += f"""
        <tr>
            <td style="padding: 8px;"><input type="checkbox" class="url-check" data-url="{url}"></td>
            <td style="padding: 8px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; color: {colors['text_primary']};">{url}</td>
            <td style="padding: 8px;"><span class="type-badge {route}">{route}</span></td>
            <td style="padding: 8px; font-size: 12px; color: {colors['text_secondary']};">{tags}</td>
            <td style="padding: 8px;">
                <button class="retry-btn" data-url="{url}" style="background: {colors['warning_bg']}; border: 1px solid {colors['warning']}; color: {colors['warning']}; padding: 4px 8px; border-radius: 4px; cursor: pointer;">↻ Retry</button>
                <button class="delete-btn" data-url="{url}" style="background: {colors['danger_bg']}; border: 1px solid {colors['danger']}; color: {colors['danger']}; padding: 4px 8px; border-radius: 4px; cursor: pointer;">× Delete</button>
            </td>
        </tr>
        """

    html += "</table>"
    return html


def render_pending_novels_html() -> str:
    colors = get_theme_colors()
    novels = queue_service.get_all_novels()
    pending_novels = [n for n in novels if n.status == "pending"]

    if not pending_novels:
        return f"<p style='color: {colors['text_secondary']};'>No pending novels</p>"

    html = f"<h3 style='color: {colors['text_primary']};'>Pending Novels (" + str(len(pending_novels)) + ")</h3><table style='width:100%;'>"
    html += f"<tr><th style='color: {colors['text_secondary']};'>URL</th><th style='color: {colors['text_secondary']};'>Chapters</th><th style='color: {colors['text_secondary']};'>Actions</th></tr>"

    for entry in pending_novels:
        url = entry.url
        start = entry.start_chapter
        end = entry.end_chapter

        html += f"""
        <tr>
            <td style="padding: 8px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; color: {colors['text_primary']};">{url}</td>
            <td style="padding: 8px; color: {colors['text_primary']};">Ch {start}-{end}</td>
            <td style="padding: 8px;">
                <button class="delete-btn" data-url="{url}" style="background: {colors['danger_bg']}; border: 1px solid {colors['danger']}; color: {colors['danger']}; padding: 4px 8px; border-radius: 4px; cursor: pointer;">× Delete</button>
            </td>
        </tr>
        """

    html += "</table>"
    return html


def render_retry_normal_html() -> str:
    retry_list = queue_service.get_retry_normal()
    colors = get_theme_colors()

    if not retry_list:
        return f"<p style='color: {colors['text_secondary']};'>No failed URLs to retry</p>"

    html = f"<h3 style='color: {colors['text_primary']};'>Retry Queue (" + str(len(retry_list)) + ")</h3><table style='width:100%;'>"
    html += f"<tr><th style='color: {colors['text_secondary']};'>URL</th><th style='color: {colors['text_secondary']};'>Error</th><th style='color: {colors['text_secondary']};'>Actions</th></tr>"

    for entry in retry_list:
        url = entry.get("url", "")
        error = (entry.get("error") or "Unknown")[:50]

        html += f"""
        <tr>
            <td style="padding: 8px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; color: {colors['text_primary']};">{url}</td>
            <td style="padding: 8px; font-size: 12px; color: {colors['danger']};">{error}</td>
            <td style="padding: 8px;">
                <button class="retry-btn" data-url="{url}" style="background: {colors['success_bg']}; border: 1px solid {colors['success']}; color: {colors['success']}; padding: 4px 8px; border-radius: 4px; cursor: pointer;">↻ Retry</button>
                <button class="delete-btn" data-url="{url}" style="background: {colors['danger_bg']}; border: 1px solid {colors['danger']}; color: {colors['danger']}; padding: 4px 8px; border-radius: 4px; cursor: pointer;">× Delete</button>
            </td>
        </tr>
        """

    html += "</table>"
    return html


def render_retry_novel_html() -> str:
    retry_list = queue_service.get_retry_novel()
    colors = get_theme_colors()

    if not retry_list:
        return f"<p style='color: {colors['text_secondary']};'>No failed novel chapters to retry</p>"

    html = f"<h3 style='color: {colors['text_primary']};'>Retry Queue (" + str(len(retry_list)) + ")</h3><table style='width:100%;'>"
    html += f"<tr><th style='color: {colors['text_secondary']};'>URL</th><th style='color: {colors['text_secondary']};'>Chapter</th><th style='color: {colors['text_secondary']};'>Error</th><th style='color: {colors['text_secondary']};'>Actions</th></tr>"

    for entry in retry_list:
        url = entry.get("url", "")
        chapter = entry.get("chapter", "N/A")
        error = (entry.get("error") or "Unknown")[:30]

        html += f"""
        <tr>
            <td style="padding: 8px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; color: {colors['text_primary']};">{url}</td>
            <td style="padding: 8px; color: {colors['text_primary']};">Ch {chapter}</td>
            <td style="padding: 8px; font-size: 12px; color: {colors['danger']};">{error}</td>
            <td style="padding: 8px;">
                <button class="retry-btn" data-url="{url}" style="background: {colors['success_bg']}; border: 1px solid {colors['success']}; color: {colors['success']}; padding: 4px 8px; border-radius: 4px; cursor: pointer;">↻ Retry</button>
                <button class="delete-btn" data-url="{url}" style="background: {colors['danger_bg']}; border: 1px solid {colors['danger']}; color: {colors['danger']}; padding: 4px 8px; border-radius: 4px; cursor: pointer;">× Delete</button>
            </td>
        </tr>
        """

    html += "</table>"
    return html
