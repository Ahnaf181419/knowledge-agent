"""
Stat Cards - Native Streamlit metrics with dark theme styling
"""

import streamlit as st
from app.container import container


def render_stats_row():
    """Render a row of stat cards"""
    hist_stats = container.history_repo.get_stats()
    queue = container.state_repo.queue
    
    extracted = hist_stats.get('normal_links', 0)
    pending = len([u for u in queue.get('urls', []) if u.get('status') == 'pending'])
    pending += len([n for n in queue.get('novels', []) if n.get('status') == 'pending'])
    words = hist_stats.get('total_words', 0)
    chapters = hist_stats.get('total_chapters', 0)
    
    daily = container.stats_repo.get_daily_activity(7)
    trend = [daily.get(d, {}).get('urls', 0) for d in sorted(daily.keys())]
    last_day = trend[-1] if trend else 0
    prev_day = trend[-2] if len(trend) > 1 else 0
    delta = last_day - prev_day if prev_day > 0 else last_day
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Extracted", 
            value=f"{extracted:,}",
            delta=f"+{delta} today" if delta > 0 else None
        )
    
    with col2:
        st.metric(label="Pending", value=f"{pending}")
    
    with col3:
        if words >= 1000000:
            words_str = f"{words/1000000:.1f}M"
        elif words >= 1000:
            words_str = f"{words/1000:.1f}K"
        else:
            words_str = f"{words:,}"
        st.metric(label="Total Words", value=words_str)
    
    with col4:
        st.metric(label="Chapters", value=f"{chapters:,}")
