from __future__ import annotations

import gradio as gr

from app.state import state
from app.theme import get_theme_colors


def create_settings_tab() -> None:
    gr.Markdown("### Settings")

    colors = get_theme_colors()
    gr.Markdown(f"""
    <div style="background: {colors['warning_bg']}; border: 1px solid {colors['warning']}; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
        <strong>⚠️ Theme changes require app restart</strong>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: {colors['text_secondary']};">Restart the application for theme changes to take effect.</p>
    </div>
    """)

    with gr.Accordion("Appearance", open=True):
        current_theme = state.get_setting("theme", "dark")
        theme_radio = gr.Radio(
            ["dark", "light"],
            label="Theme",
            value=current_theme,
        )
        theme_radio.change(
            lambda theme: state.set_setting("theme", theme),
            inputs=[theme_radio],
            outputs=[],
        )

    with gr.Accordion("Export Settings", open=False):
        export_format = gr.Dropdown(
            ["md", "txt", "json"],
            label="Default Format",
            value=state.get_setting("export_format", "md"),
        )
        export_format.change(
            lambda fmt: state.set_setting("export_format", fmt),
            inputs=[export_format],
            outputs=[],
        )

    with gr.Accordion("Scraping Behavior", open=False):
        respect_robots = gr.Checkbox(
            label="Respect robots.txt",
            value=bool(state.get_setting("respect_robots_txt", True)),
        )
        respect_robots.change(
            lambda val: state.set_setting("respect_robots_txt", val),
            inputs=[respect_robots],
            outputs=[],
        )

        concurrent_jobs = gr.Slider(
            label="Concurrent Jobs",
            minimum=1,
            maximum=5,
            step=1,
            value=state.get_setting("concurrent_jobs", 3),
        )
        concurrent_jobs.change(
            lambda val: state.set_setting("concurrent_jobs", val),
            inputs=[concurrent_jobs],
            outputs=[],
        )

        retry_count = gr.Slider(
            label="Retry Failed",
            minimum=0,
            maximum=3,
            step=1,
            value=state.get_setting("retry_count", 2),
        )
        retry_count.change(
            lambda val: state.set_setting("retry_count", val),
            inputs=[retry_count],
            outputs=[],
        )

    with gr.Accordion("Novel Settings", open=False):
        gr.Markdown("**Delay between chapters (to avoid IP blocking)**")

        with gr.Row():
            novel_delay_min = gr.Number(
                label="Min Delay (seconds)",
                minimum=30,
                maximum=180,
                value=state.get_setting("novel_delay_min", 90),
            )
            novel_delay_max = gr.Number(
                label="Max Delay (seconds)",
                minimum=60,
                maximum=300,
                value=state.get_setting("novel_delay_max", 120),
            )

        novel_delay_min.change(
            lambda val: state.set_setting("novel_delay_min", val),
            inputs=[novel_delay_min],
            outputs=[],
        )
        novel_delay_max.change(
            lambda val: state.set_setting("novel_delay_max", val),
            inputs=[novel_delay_max],
            outputs=[],
        )

    with gr.Accordion("Data Management", open=False):
        auto_save = gr.Checkbox(
            label="Auto-save queue on close",
            value=bool(state.get_setting("auto_save_queue", True)),
        )
        auto_save.change(
            lambda val: state.set_setting("auto_save_queue", val),
            inputs=[auto_save],
            outputs=[],
        )

        reset_btn = gr.Button("Clear All Settings", variant="stop")
        reset_btn.click(reset_settings)

    with gr.Accordion("Notifications", open=False):
        gr.Markdown("**System notification settings**")

        notifications_enabled = gr.Checkbox(
            label="Enable notifications",
            value=bool(state.get_setting("notifications_enabled", True)),
        )
        notifications_enabled.change(
            lambda val: state.set_setting("notifications_enabled", val),
            inputs=[notifications_enabled],
            outputs=[],
        )

        with gr.Row():
            notify_success = gr.Checkbox(
                label="On success",
                value=bool(state.get_setting("notify_on_success", True)),
            )
            notify_failure = gr.Checkbox(
                label="On failure",
                value=bool(state.get_setting("notify_on_failure", True)),
            )

        notify_success.change(
            lambda val: state.set_setting("notify_on_success", val),
            inputs=[notify_success],
            outputs=[],
        )
        notify_failure.change(
            lambda val: state.set_setting("notify_on_failure", val),
            inputs=[notify_failure],
            outputs=[],
        )

    with gr.Accordion("Scheduler", open=False):
        gr.Markdown("**Background job scheduling**")

        scheduler_enabled = gr.Checkbox(
            label="Enable scheduler",
            value=bool(state.get_setting("scheduler_enabled", False)),
        )
        scheduler_enabled.change(
            lambda val: state.set_setting("scheduler_enabled", val),
            inputs=[scheduler_enabled],
            outputs=[],
        )

    with gr.Accordion("Method Optimization", open=False):
        gr.Markdown("**Self-optimizing scraper settings**")

        auto_optimize = gr.Checkbox(
            label="Enable auto-optimization",
            value=bool(state.get_setting("auto_optimize", True)),
        )
        auto_optimize.change(
            lambda val: state.set_setting("auto_optimize", val),
            inputs=[auto_optimize],
            outputs=[],
        )

        with gr.Row():
            opt_threshold = gr.Number(
                label="Min samples for confidence",
                minimum=5,
                maximum=50,
                value=state.get_setting("optimization_threshold", 10),
            )
            success_threshold = gr.Number(
                label="Successes to promote",
                minimum=3,
                maximum=20,
                value=state.get_setting("success_promotion_threshold", 5),
            )

        opt_threshold.change(
            lambda val: state.set_setting("optimization_threshold", val),
            inputs=[opt_threshold],
            outputs=[],
        )
        success_threshold.change(
            lambda val: state.set_setting("success_promotion_threshold", val),
            inputs=[success_threshold],
            outputs=[],
        )

    with gr.Accordion("Markdown Linting", open=False):
        gr.Markdown("**Output folder markdown linting**")

        auto_lint_startup = gr.Checkbox(
            label="Auto-lint on startup",
            value=bool(state.get_setting("auto_lint_startup", False)),
        )
        auto_lint_startup.change(
            lambda val: state.set_setting("auto_lint_startup", val),
            inputs=[auto_lint_startup],
            outputs=[],
        )

        auto_lint_scrape = gr.Checkbox(
            label="Auto-lint on scrape completion",
            value=bool(state.get_setting("auto_lint_scrape", False)),
        )
        auto_lint_scrape.change(
            lambda val: state.set_setting("auto_lint_scrape", val),
            inputs=[auto_lint_scrape],
            outputs=[],
        )

        lint_output_folder_btn = gr.Button("Lint Output Folder")
        lint_status = gr.Textbox(
            label="Lint Status",
            interactive=False,
            lines=3,
        )

        def run_lint() -> str:
            from app.services.lint_service import lint_service

            results = lint_service.lint_output_folder(fix=True)
            summary = lint_service.get_status_summary(results)
            return f"Total: {summary['total']} | Fixed: {summary['fixed']} | Success: {summary['success']} | Issues: {summary['issues']} | Errors: {summary['errors']}"

        lint_output_folder_btn.click(
            run_lint,
            outputs=[lint_status],
        )

    gr.HTML("<hr>")

    gr.Markdown("#### Current Settings")
    gr.JSON(value=state.settings)


def reset_settings() -> None:
    import json

    from app.state import DEFAULT_SETTINGS, SETTINGS_FILE

    with open(SETTINGS_FILE, "w") as f:
        json.dump(DEFAULT_SETTINGS, f, indent=2)

    gr.Success("Settings reset to defaults")
