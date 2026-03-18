from __future__ import annotations

import gradio as gr

from app.config import get_ui_refresh
from app.services.scheduler_service import scheduler_service
from app.theme import get_theme_colors


def create_scheduler_tab() -> None:
    gr.Markdown("## ⏰ Scheduler")
    gr.Markdown("Manage scheduled scraping jobs")

    refresh_interval = get_ui_refresh("scheduler")

    with gr.Row():
        start_btn = gr.Button("▶ Start Scheduler", variant="primary")
        stop_btn = gr.Button("⏹ Stop Scheduler", variant="stop")
        refresh_btn = gr.Button("🔄 Refresh", size="sm")

    status_html = gr.HTML()
    jobs_html = gr.HTML()

    gr.HTML(f"<p style='font-size: 12px; color: {get_theme_colors()['text_muted']};'>Auto-refreshes every {refresh_interval} seconds</p>")

    gr.HTML("<hr>")

    gr.Markdown("### ➕ Add Scheduled Job")

    with gr.Row():
        job_name = gr.Textbox(label="Job Name", placeholder="Daily Scrape")
        job_type = gr.Radio(
            ["Interval", "Cron", "One-time"],
            label="Job Type",
            value="Interval",
        )

    with gr.Row():
        with gr.Column():
            gr.Markdown("**Interval Settings**")
            with gr.Row():
                interval_minutes = gr.Number(label="Minutes", value=30, minimum=1)
                interval_hours = gr.Number(label="Hours", value=0, minimum=0)

        with gr.Column():
            gr.Markdown("**Cron Settings**")
            with gr.Row():
                cron_hour = gr.Number(label="Hour (0-23)", value=2, minimum=0, maximum=23)
                cron_minute = gr.Number(label="Minute (0-59)", value=0, minimum=0, maximum=59)
                cron_days = gr.Textbox(
                    label="Days (mon,tue,wed,thu,fri,sat,sun)",
                    placeholder="mon,tue,wed,thu,fri",
                )

    add_job_btn = gr.Button("➕ Add Job", variant="primary")
    add_status = gr.HTML()

    def update_status() -> str:
        colors = get_theme_colors()
        is_running = scheduler_service.is_running()
        jobs = scheduler_service.get_all_jobs()
        running_jobs = scheduler_service.get_running_jobs()

        status_color = colors['success'] if is_running else colors['text_secondary']
        status_text = "Running" if is_running else "Stopped"

        html = f"""
        <div style="background: {colors['bg_secondary']}; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 18px;">●</span>
                <span style="font-weight: 600;">Scheduler Status: <span style="color: {status_color};">{status_text}</span></span>
            </div>
            <div style="margin-top: 8px; color: {colors['text_secondary']};">
                Active Jobs: {len(jobs)} | Running: {len(running_jobs)}
            </div>
        </div>
        """
        return html

    def render_jobs() -> str:
        colors = get_theme_colors()
        jobs = scheduler_service.get_all_jobs()

        if not jobs:
            return f"<p style='color: {colors['text_secondary']};'>No scheduled jobs</p>"

        border = colors['border']
        html = f"""
        <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
        <thead>
            <tr style='background: {colors['bg_tertiary']};'>
                <th style='padding: 10px; text-align: left;'>Name</th>
                <th style='padding: 10px; text-align: left;'>Type</th>
                <th style='padding: 10px; text-align: left;'>Next Run</th>
                <th style='padding: 10px; text-align: left;'>Status</th>
                <th style='padding: 10px; text-align: left;'>Actions</th>
            </tr>
        </thead>
        <tbody>
        """

        for job in jobs:
            next_run = job.next_run.strftime("%Y-%m-%d %H:%M") if job.next_run else "N/A"
            status_color = colors['success'] if job.status == "scheduled" else colors['warning']

            html += f"""
            <tr style='border-bottom: 1px solid {border};'>
                <td style='padding: 10px;'>{job.name}</td>
                <td style='padding: 10px;'>{job.trigger_type}</td>
                <td style='padding: 10px;'>{next_run}</td>
                <td style='padding: 10px; color: {status_color};'>{job.status}</td>
                <td style='padding: 10px;'>
                    <span style='color: {colors['text_secondary']};'>[Pause] [Remove]</span>
                </td>
            </tr>
            """

        html += "</tbody></table>"
        return html

    def start_scheduler():
        scheduler_service.start()
        return update_status(), render_jobs()

    def stop_scheduler():
        scheduler_service.stop()
        return update_status(), render_jobs()

    def add_job(name: str, job_type: str, mins: int, hours: int, hour: int, minute: int, days: str) -> str:
        colors = get_theme_colors()
        if not name:
            return f"<p style='color: {colors['danger']};'>Please enter a job name</p>"

        def dummy_func():
            pass

        if job_type == "Interval":
            if hours > 0 or mins > 0:
                job_id = scheduler_service.add_interval_job(
                    dummy_func,
                    minutes=mins,
                    hours=hours,
                    job_id=name.replace(" ", "_").lower(),
                    name=name,
                )
            else:
                return f"<p style='color: {colors['danger']};'>Please set interval > 0</p>"
        elif job_type == "Cron":
            job_id = scheduler_service.add_cron_job(
                dummy_func,
                job_id=name.replace(" ", "_").lower(),
                name=name,
                hour=hour,
                minute=minute,
                day_of_week=days if days else None,
            )
        else:
            return f"<p style='color: {colors['danger']};'>One-time jobs not yet supported in UI</p>"

        if job_id:
            return f"<p style='color: {colors['success']};'>✅ Added job: {name}</p>"
        return f"<p style='color: {colors['danger']};'>Failed to add job</p>"

    start_btn.click(start_scheduler, outputs=[status_html, jobs_html])
    stop_btn.click(stop_scheduler, outputs=[status_html, jobs_html])
    refresh_btn.click(lambda: (update_status(), render_jobs()), outputs=[status_html, jobs_html])

    add_job_btn.click(
        add_job,
        inputs=[job_name, job_type, interval_minutes, interval_hours, cron_hour, cron_minute, cron_days],
        outputs=[add_status],
    ).then(lambda: (update_status(), render_jobs()), outputs=[status_html, jobs_html])

    timer = gr.Timer(refresh_interval)
    timer.tick(lambda: (update_status(), render_jobs()), None, [status_html, jobs_html])

    gr.HTML("<hr>")

    gr.Markdown("### 📋 Scheduled Jobs")

    update_status()
    render_jobs()
