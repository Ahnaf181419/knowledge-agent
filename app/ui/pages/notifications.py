from __future__ import annotations

import gradio as gr

from app.config import get_ui_refresh, get_setting, update_setting
from app.services.notification_service import NotificationConfig, notification_service
from app.theme import get_theme_colors


def create_notifications_tab() -> None:
    gr.Markdown("## 🔔 Notifications")
    gr.Markdown("Configure system notification settings")

    refresh_interval = get_ui_refresh("notifications")

    gr.Markdown("### Notification Status")

    enabled = get_setting("notifications_enabled", True)
    notify_success = get_setting("notify_on_success", True)
    notify_failure = get_setting("notify_on_failure", True)
    notify_complete = get_setting("notify_on_complete", True)

    with gr.Row():
        enabled_cb = gr.Checkbox(
            label="Enable Notifications",
            value=enabled,
        )
        test_btn = gr.Button("🔔 Test Notification")

    test_status = gr.HTML()

    gr.HTML("<hr>")

    gr.Markdown("### Notification Events")

    with gr.Row():
        success_cb = gr.Checkbox(
            label="Notify on successful scrape",
            value=notify_success,
        )
        failure_cb = gr.Checkbox(
            label="Notify on scrape failure",
            value=notify_failure,
        )
        complete_cb = gr.Checkbox(
            label="Notify when batch complete",
            value=notify_complete,
        )

    gr.HTML(f"<p style='font-size: 12px; color: {get_theme_colors()['text_muted']};'>Auto-refreshes every {refresh_interval} seconds</p>")

    gr.HTML("<hr>")

    gr.Markdown("### Recent Notifications")
    log_html = gr.HTML()

    def update_enabled(enabled: bool):
        update_setting("notifications_enabled", enabled)
        config = NotificationConfig(
            enabled=enabled,
            notify_on_success=get_setting("notify_on_success", True),
            notify_on_failure=get_setting("notify_on_failure", True),
            notify_on_complete=get_setting("notify_on_complete", True),
        )
        notification_service.update_config(config)
        colors = get_theme_colors()
        return f"<p style='color: {colors['success']};'>Notifications {'enabled' if enabled else 'disabled'}</p>"

    def update_success(enabled: bool):
        update_setting("notify_on_success", enabled)
        config = NotificationConfig(
            enabled=get_setting("notifications_enabled", True),
            notify_on_success=enabled,
            notify_on_failure=get_setting("notify_on_failure", True),
            notify_on_complete=get_setting("notify_on_complete", True),
        )
        notification_service.update_config(config)
        return ""

    def update_failure(enabled: bool):
        update_setting("notify_on_failure", enabled)
        config = NotificationConfig(
            enabled=get_setting("notifications_enabled", True),
            notify_on_success=get_setting("notify_on_success", True),
            notify_on_failure=enabled,
            notify_on_complete=get_setting("notify_on_complete", True),
        )
        notification_service.update_config(config)
        return ""

    def update_complete(enabled: bool):
        update_setting("notify_on_complete", enabled)
        config = NotificationConfig(
            enabled=get_setting("notifications_enabled", True),
            notify_on_success=get_setting("notify_on_success", True),
            notify_on_failure=get_setting("notify_on_failure", True),
            notify_on_complete=enabled,
        )
        notification_service.update_config(config)
        return ""

    def send_test():
        result = notification_service.notify(
            title="Test Notification",
            message="This is a test notification from KnowledgeAgent",
        )
        colors = get_theme_colors()
        if result:
            return f"<p style='color: {colors['success']};'>✅ Test notification sent!</p>"
        return f"<p style='color: {colors['danger']};'>❌ Failed to send notification (check if plyer is installed)</p>"

    def render_log() -> str:
        colors = get_theme_colors()
        return f"""
        <div style="background: {colors['bg_secondary']}; padding: 12px; border-radius: 8px;">
            <p style="color: {colors['text_secondary']}; font-size: 12px;">No recent notifications</p>
        </div>
        """

    enabled_cb.change(update_enabled, inputs=[enabled_cb], outputs=[test_status])
    success_cb.change(update_success, inputs=[success_cb], outputs=[test_status])
    failure_cb.change(update_failure, inputs=[failure_cb], outputs=[test_status])
    complete_cb.change(update_complete, inputs=[complete_cb], outputs=[test_status])
    test_btn.click(send_test, outputs=[test_status])

    timer = gr.Timer(refresh_interval)
    timer.tick(render_log, None, [log_html])

    render_log()
