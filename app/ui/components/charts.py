from __future__ import annotations

import pandas as pd  # noqa: F401 - Prevents circular import with plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots


METHOD_COLORS = {
    "simple_http": "#3b82f6",
    "playwright": "#8b5cf6",
    "playwright_alt": "#06b6d4",
    "playwright_tls": "#f59e0b",
    "cloudscraper": "#10b981",
}

METHOD_LABELS = {
    "simple_http": "Simple HTTP",
    "playwright": "Playwright",
    "playwright_alt": "Playwright Alt",
    "playwright_tls": "Playwright TLS",
    "cloudscraper": "CloudScraper",
}


def render_radar_chart(method_stats: dict) -> go.Figure:
    """Create radar chart comparing methods across multiple dimensions."""
    if not method_stats:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig

    categories = ["Success Rate", "Speed", "Word Efficiency", "Usage"]
    
    fig = go.Figure()
    
    for method, data in method_stats.items():
        attempts = data.get("total_attempts", 0)
        if attempts == 0:
            continue
            
        success_rate = data.get("success_rate", 0)
        avg_time = data.get("avg_time_ms", 1)
        avg_words = data.get("total_words", 0) / attempts if attempts > 0 else 0
        
        speed_score = max(0, 100 - (avg_time / 50))
        word_score = min(avg_words / 50 * 100, 100)
        usage_score = min(attempts / 10 * 100, 100)
        
        values = [success_rate, speed_score, word_score, usage_score]
        values.append(data.get("efficiency_score", 0))
        
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name=METHOD_LABELS.get(method, method),
            line_color=METHOD_COLORS.get(method, "#888"),
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
            )
        ),
        showlegend=True,
        height=400,
        margin=dict(t=40, b=40, l=40, r=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#374151"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
    )
    
    return fig


def render_method_bar_chart(method_stats: dict) -> go.Figure:
    """Create grouped bar chart comparing success/fail per method."""
    if not method_stats:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig

    methods = []
    success_counts = []
    fail_counts = []
    
    for method, data in sorted(method_stats.items(), key=lambda x: x[1].get("total_attempts", 0), reverse=True):
        if data.get("total_attempts", 0) == 0:
            continue
        methods.append(METHOD_LABELS.get(method, method))
        success_counts.append(data.get("success", 0))
        fail_counts.append(data.get("failed", 0))

    if not methods:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig

    fig = go.Figure(data=[
        go.Bar(name="Success", x=methods, y=success_counts, marker_color="#22c55e"),
        go.Bar(name="Failed", x=methods, y=fail_counts, marker_color="#ef4444"),
    ])

    fig.update_layout(
        barmode="group",
        height=350,
        margin=dict(t=20, b=40, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#374151"),
        xaxis=dict(title="", tickangle=-45),
        yaxis=dict(title="Count"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
        ),
        barcornerradius=4,
    )
    
    return fig


def render_success_pie(summary_stats: dict) -> go.Figure:
    """Create donut chart for success vs failed."""
    success = summary_stats.get("total_success", 0)
    failed = summary_stats.get("total_failed", 0)
    total = success + failed
    
    if total == 0:
        fig = go.Figure()
        fig.add_annotation(text="No data yet", showarrow=False)
        return fig

    fig = go.Figure(data=[
        go.Pie(
            labels=["Success", "Failed"],
            values=[success, failed],
            marker=dict(colors=["#22c55e", "#ef4444"]),
            hole=0.6,
            textinfo="label+percent",
            textposition="outside",
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}<extra></extra>",
        )
    ])

    fig.update_layout(
        height=280,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        annotations=[
            dict(
                text=f"<b>{summary_stats.get('success_rate', 0):.1f}%</b>",
                x=0.5,
                y=0.5,
                font_size=24,
                showarrow=False,
                font_color="#22c55e",
            )
        ],
    )
    
    return fig


def render_daily_line_chart(daily_data: dict) -> go.Figure:
    """Create line chart showing daily activity."""
    if not daily_data:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig

    dates = sorted(daily_data.keys(), reverse=True)[-14:]
    dates = sorted(dates)
    
    success_counts = [daily_data.get(d, {}).get("success", 0) for d in dates]
    failed_counts = [daily_data.get(d, {}).get("failed", 0) for d in dates]
    total_counts = [daily_data.get(d, {}).get("urls", 0) for d in dates]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=success_counts,
        mode="lines+markers",
        name="Success",
        line=dict(color="#22c55e", width=3),
        marker=dict(size=8),
        fill="tozeroy",
        fillcolor="rgba(34, 197, 94, 0.1)",
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=failed_counts,
        mode="lines+markers",
        name="Failed",
        line=dict(color="#ef4444", width=2, dash="dot"),
        marker=dict(size=6),
    ))

    fig.update_layout(
        height=300,
        margin=dict(t=20, b=40, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#374151"),
        xaxis=dict(
            title="",
            tickformat="%m/%d",
            tickangle=-45,
        ),
        yaxis=dict(title="URLs"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
        ),
        hovermode="x unified",
    )
    
    return fig


def render_efficiency_bar(method_stats: dict) -> go.Figure:
    """Create horizontal bar chart for efficiency scores."""
    if not method_stats:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig

    methods = []
    scores = []
    colors = []
    
    for method, data in sorted(method_stats.items(), key=lambda x: x[1].get("efficiency_score", 0), reverse=True):
        if data.get("total_attempts", 0) == 0:
            continue
        methods.append(METHOD_LABELS.get(method, method))
        scores.append(data.get("efficiency_score", 0))
        colors.append(METHOD_COLORS.get(method, "#888"))

    if not methods:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig

    fig = go.Figure(go.Bar(
        x=scores,
        y=methods,
        orientation="h",
        marker_color=colors,
        text=[f"{s:.1f}" for s in scores],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Efficiency: %{x}<extra></extra>",
    ))

    fig.update_layout(
        height=max(200, len(methods) * 50),
        margin=dict(t=10, b=40, l=120, r=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#374151"),
        xaxis=dict(title="Efficiency Score", range=[0, 110]),
        yaxis=dict(title=""),
        barcornerradius=4,
    )
    
    return fig
