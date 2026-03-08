"""
Main Dashboard Page - Overview Only
Clean layout focused on key metrics and quick status
Method-specific analytics moved to Analytics tab
"""

import streamlit as st
from app.container import container
from app.components.stat_cards import render_stats_row
from app.components.gauges import create_semi_gauge, create_success_rate_gauge
from app.components.api_card import render_api_usage_card
from app.components.shadcn_helpers import card_container


def render():
    """Render main dashboard overview"""
    
    st.title("Dashboard")
    
    col_title, col_refresh = st.columns([5, 1])
    with col_title:
        st.caption("Overview of your knowledge extraction")
    with col_refresh:
        if st.button("🔄 Refresh", key="refresh_dashboard", use_container_width=True):
            st.rerun()
    
    render_stats_row()
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        with card_container(key="gauge_api"):
            from app.api_tracker import get_api_usage
            usage = get_api_usage()
            fig = create_semi_gauge(usage['calls_used'], usage['calls_limit'], "API Usage")
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        with card_container(key="gauge_success"):
            queue = container.state_repo.queue
            completed = len([u for u in queue.get('urls', []) if u.get('status') == 'completed'])
            failed = len([u for u in queue.get('urls', []) if u.get('status') == 'failed'])
            rate = (completed / (completed + failed) * 100) if (completed + failed) > 0 else 100
            fig = create_success_rate_gauge(rate)
            st.plotly_chart(fig, width="stretch")
    
    st.divider()
    
    render_api_usage_card()
    
    st.divider()
    
    with card_container(key="recent_activity"):
        st.markdown('<div class="section-header">Recent Activity</div>', unsafe_allow_html=True)
        recent = container.stats_repo.get_recent(10)
        
        if recent:
            for item in recent:
                status_icon = "✓" if item.success else "✗"
                status_color = "#299c46" if item.success else "#c4172c"
                method = item.method or 'unknown'
                time_str = f"{item.time_ms}ms"
                url = item.url or ''
                
                method_labels = {
                    "simple_http": ("simple_http", "#6ba3f5"),
                    "playwright": ("playwright", "#c084fc"),
                    "playwright_alt": ("playwright_alt", "#8b5cf6"),
                    "webscrapingapi": ("webscrapingapi", "#fb923c")
                }
                method_label, method_color = method_labels.get(method, (method, "#8e8e8e"))
                
                c1, c2 = st.columns([4, 2])
                with c1:
                    st.caption(f"<span style='color:{status_color}'>{status_icon}</span> {url[:45]}{'...' if len(url) > 45 else ''}", unsafe_allow_html=True)
                with c2:
                    st.caption(f"`{method_label}` | {time_str}")
        else:
            st.info("No recent activity. Start scraping to see results here.")
    
    st.divider()
    
    st.caption("📊 For detailed method analytics, visit the **Analytics** tab")
