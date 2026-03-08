"""
Analytics Charts Module

Chart functions for the Analytics tab:
- Radar/Spider chart for method comparison
- Stacked area chart for method usage over time
- Grouped bar chart for success/fail ratio
- Performance comparison charts
"""

import plotly.graph_objects as go
from datetime import datetime
from typing import Optional

METHOD_COLORS = {
    "simple_http": "#5c9eff",
    "playwright": "#a78bfa",
    "playwright_alt": "#c4b5fd",
    "webscrapingapi": "#fbbf24"
}

SUCCESS_COLOR = "#4ade80"
FAIL_COLOR = "#f87171"
GRID_COLOR = "#2d3a52"
TEXT_COLOR = "#a8b2c1"
TEXT_PRIMARY = "#e8eaed"

METHOD_LABELS = {
    "simple_http": "Simple HTTP",
    "playwright": "Playwright",
    "playwright_alt": "Playwright Alt",
    "webscrapingapi": "WebScrapingAPI"
}


def create_method_radar_chart(method_comparison: dict) -> go.Figure:
    """
    Radar/Spider chart comparing methods across 3 metrics:
    - Success Rate
    - Speed Score
    - Efficiency Score
    """
    categories = ['Success Rate', 'Speed Score', 'Efficiency Score']
    
    fig = go.Figure()
    
    for method, values in method_comparison.items():
        color = METHOD_COLORS.get(method, "#8e8e8e")
        label = METHOD_LABELS.get(method, method)
        
        r_values = [
            values.get('success_rate', 0),
            values.get('speed_score', 0),
            values.get('efficiency_score', 0)
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=r_values,
            theta=categories,
            fill='toself',
            name=label,
            line_color=color,
            opacity=0.7
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color=TEXT_COLOR, size=10),
                gridcolor=GRID_COLOR,
                linecolor=GRID_COLOR
            ),
            angularaxis=dict(
                tickfont=dict(color=TEXT_COLOR, size=11),
                gridcolor=GRID_COLOR,
                linecolor=GRID_COLOR
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=True,
        height=320,
        margin=dict(l=50, r=50, t=30, b=30),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
            font=dict(color=TEXT_COLOR, size=10)
        ),
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def create_method_pie_chart(method_stats: dict) -> go.Figure:
    """Create pie chart of scraping method distribution"""
    labels = []
    values = []
    colors = []
    
    for method, data in method_stats.items():
        success = data.get('success', 0)
        if success > 0:
            labels.append(METHOD_LABELS.get(method, method))
            values.append(success)
            colors.append(METHOD_COLORS.get(method, "#8e8e8e"))
    
    if not labels:
        fig = go.Figure()
        fig.add_annotation(text="No data yet", showarrow=False, font=dict(color=TEXT_COLOR, size=14))
    else:
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.5,
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(color=TEXT_PRIMARY, size=11)
        )])
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_PRIMARY),
        height=220,
        margin=dict(l=20, r=20, t=10, b=10),
        showlegend=False
    )
    
    return fig


def create_activity_timeline(daily_data: dict) -> go.Figure:
    """Create line chart of daily scraping activity"""
    dates = sorted(daily_data.keys())
    urls = [daily_data[d].get('urls', 0) for d in dates]
    success = [daily_data[d].get('success', 0) for d in dates]
    
    display_dates = [datetime.strptime(d, "%Y-%m-%d").strftime("%b %d") for d in dates]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=display_dates,
        y=urls,
        mode='lines+markers',
        name='Total URLs',
        line=dict(color="#5c9eff", width=2),
        marker=dict(size=8, color="#5c9eff"),
        fill='tozeroy',
        fillcolor='rgba(92, 158, 255, 0.1)'
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_PRIMARY),
        height=200,
        margin=dict(l=40, r=20, t=10, b=40),
        xaxis=dict(
            showgrid=False,
            tickcolor=GRID_COLOR,
            tickfont=dict(color=TEXT_COLOR, size=10)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickcolor=GRID_COLOR,
            tickfont=dict(color=TEXT_COLOR, size=10)
        )
    )
    
    return fig


def create_method_timeline_stacked(method_timeline: dict) -> go.Figure:
    """Stacked area chart showing method usage over time"""
    dates = sorted(method_timeline.keys())
    display_dates = [datetime.strptime(d, "%Y-%m-%d").strftime("%b %d") for d in dates]
    
    fig = go.Figure()
    
    for method in ["simple_http", "playwright", "playwright_alt", "webscrapingapi"]:
        color = METHOD_COLORS.get(method, "#8e8e8e")
        label = METHOD_LABELS.get(method, method)
        
        values = []
        for date in dates:
            day_data = method_timeline.get(date, {}).get(method, {})
            values.append(day_data.get('success', 0) + day_data.get('failed', 0))
        
        fig.add_trace(go.Scatter(
            x=display_dates,
            y=values,
            name=label,
            mode='lines',
            stackgroup='one',
            line=dict(color=color, width=1),
            fillcolor=color
        ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_PRIMARY),
        height=200,
        margin=dict(l=40, r=20, t=10, b=40),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color=TEXT_COLOR, size=10)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickfont=dict(color=TEXT_COLOR, size=10)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=TEXT_COLOR, size=9)
        )
    )
    
    return fig


def create_domain_bar_chart(domain_stats: dict, limit: int = 5) -> go.Figure:
    """Create horizontal bar chart of top domains"""
    sorted_domains = sorted(
        domain_stats.items(),
        key=lambda x: sum(m.get('success', 0) + m.get('failed', 0) for m in x[1].values()),
        reverse=True
    )[:limit]
    
    if not sorted_domains:
        fig = go.Figure()
        fig.add_annotation(text="No data yet", showarrow=False, font=dict(color=TEXT_COLOR, size=14))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=180)
        return fig
    
    domains = [d[0].replace('www.', '')[:25] for d in sorted_domains]
    
    success = []
    failed = []
    for _, methods in sorted_domains:
        s = sum(m.get('success', 0) for m in methods.values())
        f = sum(m.get('failed', 0) for m in methods.values())
        success.append(s)
        failed.append(f)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=domains,
        x=success,
        name='Success',
        orientation='h',
        marker=dict(color=SUCCESS_COLOR),
        text=success,
        textposition='auto',
        textfont=dict(color='#ffffff', size=10)
    ))
    
    fig.add_trace(go.Bar(
        y=domains,
        x=failed,
        name='Failed',
        orientation='h',
        marker=dict(color=FAIL_COLOR),
        text=failed if any(f > 0 for f in failed) else None,
        textposition='auto',
        textfont=dict(color='#ffffff', size=10)
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_PRIMARY),
        height=200,
        margin=dict(l=90, r=20, t=10, b=20),
        barmode='stack',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=TEXT_COLOR, size=10)
        ),
        xaxis=dict(
            showgrid=True, 
            gridcolor=GRID_COLOR,
            tickfont=dict(color=TEXT_COLOR, size=10)
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(color=TEXT_COLOR, size=10)
        )
    )
    
    return fig


def create_success_fail_ratio_chart(method_stats: dict) -> go.Figure:
    """Grouped bar chart showing success/fail ratio per method"""
    methods = []
    success_vals = []
    failed_vals = []
    colors_success = []
    colors_failed = []
    
    for method in ["simple_http", "playwright", "playwright_alt", "webscrapingapi"]:
        data = method_stats.get(method, {})
        if data.get('total_attempts', 0) > 0:
            methods.append(METHOD_LABELS.get(method, method))
            success_vals.append(data.get('success', 0))
            failed_vals.append(data.get('failed', 0))
            colors_success.append("#299c46")
            colors_failed.append("#c4172c")
    
    if not methods:
        fig = go.Figure()
        fig.add_annotation(text="No data yet", showarrow=False, font=dict(color=TEXT_COLOR, size=14))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=200)
        return fig
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=methods,
        y=success_vals,
        name='Success',
        marker_color=SUCCESS_COLOR,
        text=success_vals,
        textposition='auto',
        textfont=dict(color='#ffffff', size=10)
    ))
    
    fig.add_trace(go.Bar(
        x=methods,
        y=failed_vals,
        name='Failed',
        marker_color=FAIL_COLOR,
        text=failed_vals if any(f > 0 for f in failed_vals) else None,
        textposition='auto',
        textfont=dict(color='#ffffff', size=10)
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_PRIMARY),
        height=200,
        margin=dict(l=40, r=20, t=10, b=40),
        barmode='group',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=TEXT_COLOR, size=10)
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color=TEXT_COLOR, size=10)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickfont=dict(color=TEXT_COLOR, size=10)
        )
    )
    
    return fig


def create_avg_time_comparison_chart(method_stats: dict) -> go.Figure:
    """Bar chart comparing average extraction time per method"""
    methods = []
    avg_times = []
    colors = []
    
    for method in ["simple_http", "playwright", "playwright_alt", "webscrapingapi"]:
        data = method_stats.get(method, {})
        if data.get('total_attempts', 0) > 0:
            methods.append(METHOD_LABELS.get(method, method))
            avg_times.append(data.get('avg_time_ms', 0))
            colors.append(METHOD_COLORS.get(method, "#8e8e8e"))
    
    if not methods:
        fig = go.Figure()
        fig.add_annotation(text="No data yet", showarrow=False, font=dict(color=TEXT_COLOR, size=14))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=200)
        return fig
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=methods,
        y=avg_times,
        marker_color=colors,
        text=[f"{t}ms" for t in avg_times],
        textposition='auto',
        textfont=dict(color='#ffffff', size=10)
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_PRIMARY),
        height=200,
        margin=dict(l=40, r=20, t=10, b=40),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color=TEXT_COLOR, size=10)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickfont=dict(color=TEXT_COLOR, size=10),
            title=dict(text='Avg Time (ms)', font=dict(color=TEXT_COLOR, size=10))
        )
    )
    
    return fig


def create_error_pie_chart(error_analysis: dict) -> go.Figure:
    """Pie chart showing errors by method"""
    labels = []
    values = []
    
    for method, count in error_analysis.get('by_method', {}).items():
        if count > 0:
            labels.append(METHOD_LABELS.get(method, method))
            values.append(count)
    
    if not labels:
        fig = go.Figure()
        fig.add_annotation(text="No errors", showarrow=False, font=dict(color=SUCCESS_COLOR, size=14))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=180)
        return fig
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textinfo='label+percent',
        textposition='outside',
        textfont=dict(color=TEXT_PRIMARY, size=10),
        marker=dict(colors=[METHOD_COLORS.get(m, "#6b7280") for m in error_analysis.get('by_method', {}).keys() if error_analysis['by_method'].get(m, 0) > 0])
    )])
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_PRIMARY),
        height=180,
        margin=dict(l=20, r=20, t=10, b=10),
        showlegend=False
    )
    
    return fig
