from __future__ import annotations

import gradio as gr

from app.config import get_ui_refresh
from app.services.history_service import history_service
from app.services.queue_service import queue_service
from app.theme import get_theme_colors
from scraper.router import route_url
from utils.validators import is_valid_url, parse_tags


def create_add_links_tab() -> None:
    gr.Markdown("## ➕ Add URLs")

    with gr.Row():
        with gr.Column(scale=3):
            create_normal_input()
            gr.HTML("<hr>")
            create_novel_input()
        with gr.Column(scale=1):
            create_sidebar()


def create_normal_input() -> None:
    gr.Markdown("### Normal Links")

    with gr.Row():
        urls_input = gr.Textbox(
            label="Paste URLs (one per line)",
            placeholder="https://en.wikipedia.org/wiki/Mars\nhttps://medium.com/my-article",
            lines=5,
            scale=3,
        )
        tags_input = gr.Textbox(
            label="Tags (comma separated)",
            placeholder="AI, technology, science",
            lines=1,
            scale=2,
        )

    with gr.Row():
        add_btn = gr.Button("➕ Add URLs", variant="primary")
        clear_btn = gr.Button("🗑️ Clear")

    status_output = gr.HTML()

    def handle_add(urls_text: str, tags_text: str):
        result = add_normal_urls(urls_text, tags_text)
        return "", get_queue_sidebar_html()

    add_btn.click(
        handle_add,
        inputs=[urls_input, tags_input],
        outputs=[urls_input, status_output],
    )


def create_novel_input() -> None:
    gr.Markdown("### Novel Links")

    with gr.Row():
        novel_url_input = gr.Textbox(
            label="Novel URL",
            placeholder="https://example.com/novel/chapters",
            scale=3,
        )
        tags_input = gr.Textbox(
            label="Tags (comma separated)",
            placeholder="fantasy, xianxia, romance",
            lines=1,
            scale=2,
        )

    with gr.Row():
        with gr.Column(scale=1):
            start_chapter = gr.Number(label="Start Chapter", value=1, minimum=1)
        with gr.Column(scale=1):
            end_chapter = gr.Number(label="End Chapter", value=10, minimum=1)

    with gr.Row():
        add_novel_btn = gr.Button("➕ Add Novel", variant="primary")
        clear_novel_btn = gr.Button("🗑️ Clear")

    novel_status_output = gr.HTML()

    def handle_add_novel(url: str, tags: str, start: int, end: int):
        result = add_novel_url(url, tags, start, end)
        return "", get_queue_sidebar_html()

    add_novel_btn.click(
        handle_add_novel,
        inputs=[novel_url_input, tags_input, start_chapter, end_chapter],
        outputs=[novel_url_input, novel_status_output],
    )


def create_sidebar() -> None:
    gr.Markdown("### 🚀 Start Scraping")
    start_scrape_btn = gr.Button("🚀 Start Scraping Now", variant="primary", size="lg")
    scrape_status = gr.HTML(f"<p style='color: {get_theme_colors()['text_muted']};'>Click to begin scraping pending URLs</p>")

    gr.HTML("<hr>")
    gr.Markdown("### 📋 Queue Status")
    queue_html = gr.HTML(value=get_queue_sidebar_html)

    gr.HTML("<hr>")
    gr.Markdown("### 📊 Statistics")
    stats_html = gr.HTML(value=get_stats_html)

    gr.HTML("<hr>")
    gr.Markdown("### 🔄 Auto-Refresh")

    refresh_interval = get_ui_refresh("add_urls")
    gr.HTML(f"<p style='font-size: 12px; color: {get_theme_colors()['text_muted']};'>Queue status refreshes every {refresh_interval} seconds</p>")

    def handle_start_scrape():
        return start_scrape()

    start_scrape_btn.click(
        handle_start_scrape,
        outputs=[scrape_status, queue_html],
    )

    timer = gr.Timer(refresh_interval)
    timer.tick(
        get_queue_sidebar_html,
        None,
        [queue_html],
    )

    stats_timer = gr.Timer(refresh_interval)
    stats_timer.tick(
        get_stats_html,
        None,
        [stats_html],
    )


def get_queue_sidebar_html() -> str:
    colors = get_theme_colors()
    stats = queue_service.get_stats()

    return f"""
    <div style="display: flex; flex-direction: column; gap: 8px;">
        <div style="background: {colors['warning_bg']}; padding: 12px; border-radius: 8px; border-left: 4px solid {colors['warning']};">
            <div style="font-size: 12px; color: {colors['text_secondary']};">Processing</div>
            <div style="font-size: 24px; font-weight: 600; color: {colors['warning']};">{stats.processing}</div>
        </div>
        <div style="background: {colors['info_bg']}; padding: 12px; border-radius: 8px; border-left: 4px solid {colors['primary']};">
            <div style="font-size: 12px; color: {colors['text_secondary']};">Pending</div>
            <div style="font-size: 24px; font-weight: 600; color: {colors['info']};">{stats.pending}</div>
        </div>
        <div style="background: {colors['success_bg']}; padding: 12px; border-radius: 8px; border-left: 4px solid {colors['success']};">
            <div style="font-size: 12px; color: {colors['text_secondary']};">Completed</div>
            <div style="font-size: 24px; font-weight: 600; color: {colors['success']};">{stats.completed}</div>
        </div>
        <div style="background: {colors['danger_bg']}; padding: 12px; border-radius: 8px; border-left: 4px solid {colors['danger']};">
            <div style="font-size: 12px; color: {colors['text_secondary']};">Failed</div>
            <div style="font-size: 24px; font-weight: 600; color: {colors['danger']};">{stats.failed}</div>
        </div>
        <div style="background: #fdf2f8; padding: 12px; border-radius: 8px; border-left: 4px solid #ec4899;">
            <div style="font-size: 12px; color: {colors['text_secondary']};">Novels</div>
            <div style="font-size: 24px; font-weight: 600; color: #db2777;">{stats.total_novels}</div>
        </div>
    </div>
    """


def get_stats_html() -> str:
    colors = get_theme_colors()
    try:
        stats = history_service.get_stats()
        return f"""
        <div style="display: flex; flex-direction: column; gap: 8px;">
            <div style="background: {colors['bg_secondary']}; padding: 10px; border-radius: 6px;">
                <span style="color: {colors['text_secondary']}; font-size: 12px;">Extracted:</span>
                <strong>{stats.get('normal_links', 0)}</strong>
            </div>
            <div style="background: {colors['bg_secondary']}; padding: 10px; border-radius: 6px;">
                <span style="color: {colors['text_secondary']}; font-size: 12px;">Novels:</span>
                <strong>{stats.get('novels', 0)}</strong>
            </div>
            <div style="background: {colors['bg_secondary']}; padding: 10px; border-radius: 6px;">
                <span style="color: {colors['text_secondary']}; font-size: 12px;">Chapters:</span>
                <strong>{stats.get('total_chapters', 0)}</strong>
            </div>
            <div style="background: {colors['bg_secondary']}; padding: 10px; border-radius: 6px;">
                <span style="color: {colors['text_secondary']}; font-size: 12px;">Words:</span>
                <strong>{stats.get('total_words', 0):,}</strong>
            </div>
        </div>
        """
    except Exception:
        return "<p>No statistics available</p>"


def start_scrape() -> tuple[str, str]:
    colors = get_theme_colors()
    pending = queue_service.get_pending()

    if not pending:
        return f"<p style='color: {colors['warning']};'>⚠️ No pending URLs to scrape</p>", get_queue_sidebar_html()

    job_id = queue_service.start_scrape()

    if job_id:
        return f"<p style='color: {colors['success']};'>✅ Started scraping {len(pending)} URL(s)</p>", get_queue_sidebar_html()
    else:
        return f"<p style='color: {colors['warning']};'>⚠️ Could not start scraping</p>", get_queue_sidebar_html()


def add_normal_urls(urls_text: str, tags_input: str) -> str:
    if not urls_text.strip():
        gr.Warning("Please enter at least one URL")
        return ""

    tags = parse_tags(tags_input)
    urls = [u.strip() for u in urls_text.split("\n") if u.strip()]

    added = 0
    already_extracted = 0
    in_queue = 0
    invalid = 0

    for url in urls:
        if not is_valid_url(url):
            invalid += 1
            continue

        route = route_url(url)
        if route == "skip":
            invalid += 1
            continue

        if history_service.is_extracted(url):
            already_extracted += 1
            continue

        if queue_service.url_in_queue(url):
            in_queue += 1
            continue

        if queue_service.add_url(url, "normal", tags):
            added += 1

    messages = []
    if added > 0:
        messages.append(f"Added {added} URL(s)")
    if already_extracted > 0:
        messages.append(f"Skipped {already_extracted} already extracted")
    if in_queue > 0:
        messages.append(f"Skipped {in_queue} in queue")
    if invalid > 0:
        messages.append(f"Skipped {invalid} invalid")

    if messages:
        gr.Success(" | ".join(messages))

    return ""


def add_novel_url(url: str, tags_text: str, start_chapter: int, end_chapter: int) -> str:
    if not url.strip():
        gr.Warning("Please enter a novel URL")
        return ""

    if not is_valid_url(url):
        gr.Warning("Invalid URL")
        return ""

    tags = parse_tags(tags_text)

    if queue_service.novel_in_queue(url):
        gr.Warning("URL already in queue")
        return ""

    queue_service.add_novel(url, start_chapter, end_chapter, tags)

    gr.Success(f"Added novel: {url} (Chapters {start_chapter}-{end_chapter})")
    return ""
