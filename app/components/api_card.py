"""
API Usage Card - Native Streamlit components with dark theme
"""

import streamlit as st


def render_api_usage_card():
    """Render API usage card using native Streamlit components"""
    from app.api_tracker import get_api_usage, get_next_reset_date
    
    usage = get_api_usage()
    
    used = usage['calls_used']
    limit = usage['calls_limit']
    remaining = usage['remaining']
    pct = usage['percentage']
    
    st.markdown("**WebScrapingAPI**")
    st.caption("Monthly API Usage")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Used", f"{used:,}")
    
    with col2:
        st.metric("Remaining", f"{remaining:,}")
    
    with col3:
        st.metric("Limit", f"{limit:,}")
    
    st.progress(pct / 100)
    st.caption(f"{pct:.1f}% used  |  Resets: {get_next_reset_date()}")
