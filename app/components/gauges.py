"""
Semi-Circle Gauges using Plotly
Soft dark theme styling
"""

import plotly.graph_objects as go

SUCCESS_COLOR = "#4ade80"
WARNING_COLOR = "#fbbf24"
ERROR_COLOR = "#f87171"
ACCENT_COLOR = "#5c9eff"
TEXT_COLOR = "#a8b2c1"
TEXT_PRIMARY = "#e8eaed"
BG_COLOR = "#16213e"
BORDER_COLOR = "#2d3a52"


def create_semi_gauge(value: float, max_value: float, title: str, 
                      color_steps: list = None) -> go.Figure:
    """
    Create a semi-circle gauge
    """
    if color_steps is None:
        color_steps = [
            (0.7, SUCCESS_COLOR),
            (0.9, WARNING_COLOR),
            (1.0, ERROR_COLOR)
        ]
    
    steps = []
    prev = 0
    for step in color_steps:
        steps.append({
            'range': [prev, max_value * step[0]],
            'color': step[1]
        })
        prev = max_value * step[0]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 13, 'color': TEXT_COLOR}},
        number={'font': {'size': 28, 'color': TEXT_PRIMARY}, 'suffix': f"/{int(max_value):,}"},
        gauge={
            'axis': {'range': [0, max_value], 'tickwidth': 1, 'tickcolor': BORDER_COLOR},
            'bgcolor': BG_COLOR,
            'steps': steps,
            'threshold': {
                'line': {'color': "#ffffff", 'width': 2},
                'thickness': 0.75,
                'value': value
            },
            'bar': {'color': ACCENT_COLOR}
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        height=160,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig


def create_success_rate_gauge(rate: float) -> go.Figure:
    """Create success rate gauge (0-100%)"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rate,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Success Rate", 'font': {'size': 13, 'color': TEXT_COLOR}},
        number={'font': {'size': 28, 'color': TEXT_PRIMARY}, 'suffix': "%"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': BORDER_COLOR},
            'bgcolor': BG_COLOR,
            'steps': [
                {'range': [0, 50], 'color': "rgba(248, 113, 113, 0.2)"},
                {'range': [50, 80], 'color': "rgba(251, 191, 36, 0.2)"},
                {'range': [80, 100], 'color': "rgba(74, 222, 128, 0.2)"}
            ],
            'threshold': {
                'line': {'color': "#ffffff", 'width': 2},
                'thickness': 0.75,
                'value': rate
            },
            'bar': {'color': SUCCESS_COLOR if rate >= 80 else WARNING_COLOR if rate >= 50 else ERROR_COLOR}
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        height=160,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig
