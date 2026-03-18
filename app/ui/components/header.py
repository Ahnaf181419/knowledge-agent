from __future__ import annotations

import gradio as gr

from app.state import state


def render_header() -> None:
    current_theme = state.get_setting("theme", "dark")

    with gr.Row(elem_classes=["header-row"]):
        with gr.Column(scale=8):
            gr.Markdown(
                """
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 28px;">🧠</span>
                    <span style="font-size: 22px; font-weight: 600; color: #3b82f6;">KnowledgeAgent</span>
                </div>
                """,
                elem_classes=["main-title"],
            )
        with gr.Column(scale=2):
            theme_btn = gr.Button(
                "🌙" if current_theme == "dark" else "☀️",
                size="sm",
                variant="secondary",
            )
            theme_btn.click(
                lambda: (
                    state.set_setting("theme", "light" if current_theme == "dark" else "dark"),
                    gr.update(value="☀️" if current_theme == "dark" else "🌙"),
                ),
                inputs=[],
                outputs=[theme_btn],
            )
