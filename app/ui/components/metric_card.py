from __future__ import annotations

import gradio as gr


def create_metric_card(
    label: str,
    value: str | int,
    delta: str | None = None,
    icon: str = "📊",
) -> gr.Component:
    gr.Markdown(f"**{icon} {label}**")
    gr.Markdown(f"### {value}")
    if delta:
        gr.Markdown(f"_{delta}_")
    return gr.Markdown("")


def render_stats_row() -> list[gr.Component]:
    from app.services.history_service import history_service

    stats = history_service.get_stats()

    with gr.Row():
        create_metric_card("Total Extracted", stats.get("normal_links", 0), icon="📄")
        create_metric_card("Novels", stats.get("novels", 0), icon="📚")
        create_metric_card("Chapters", stats.get("total_chapters", 0), icon="📑")
        create_metric_card("Total Words", f"{stats.get('total_words', 0):,}", icon="📝")

    return []


def render_queue_stats() -> list[gr.Component]:
    from app.state import state

    queue = state.queue
    urls = queue.get("urls", [])
    novels = queue.get("novels", [])

    pending = len([u for u in urls if u.get("status") == "pending"])
    completed = len([u for u in urls if u.get("status") == "completed"])
    failed = len([u for u in urls if u.get("status") == "failed"])

    with gr.Row():
        create_metric_card("Pending", pending, icon="⏳")
        create_metric_card("Completed", completed, icon="✅")
        create_metric_card("Failed", failed, icon="❌")
        create_metric_card("Novels", len(novels), icon="📚")

    return []
