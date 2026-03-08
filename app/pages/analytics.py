"""
Analytics Page - Comprehensive scraping method statistics

Features:
- Time period filtering (All Time, 7/15/30/90/180/365 days)
- Method comparison radar chart
- Efficiency scoring table
- Stacked area chart for method usage over time
- Success/fail ratio charts
- Domain analysis
- Error analysis
- Recent activity list
"""

import streamlit as st
from app.container import container
from app.components.analytics_charts import (
    create_method_radar_chart,
    create_method_pie_chart,
    create_activity_timeline,
    create_method_timeline_stacked,
    create_domain_bar_chart,
    create_success_fail_ratio_chart,
    create_avg_time_comparison_chart,
    create_error_pie_chart
)
from app.components.shadcn_helpers import card_container

TIME_PERIODS = [
    ("All Time", None),
    ("Last 7 days", 7),
    ("Last 15 days", 15),
    ("Last 30 days", 30),
    ("Last 90 days", 90),
    ("Last 180 days", 180),
    ("Last 365 days", 365)
]

METHOD_LABELS = {
    "simple_http": "Simple HTTP",
    "playwright": "Playwright",
    "playwright_alt": "Playwright Alt",
    "webscrapingapi": "WebScrapingAPI"
}


def render():
    """Render the Analytics page"""
    
    st.title("Analytics")
    
    col_title, col_period, col_refresh = st.columns([3, 2, 1])
    with col_title:
        st.caption("Scraping method performance and trends")
    with col_period:
        selected_period = st.select_slider(
            "Time Period",
            options=[p[0] for p in TIME_PERIODS],
            value="All Time",
            key="analytics_period"
        )
    with col_refresh:
        if st.button("🔄 Refresh", key="refresh_analytics", use_container_width=True):
            st.rerun()
    
    days = next((p[1] for p in TIME_PERIODS if p[0] == selected_period), None)
    
    summary = container.stats_repo.get_summary_stats(days)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Attempts", summary.get('total_attempts', 0))
    with col2:
        success_rate = summary.get('success_rate', 0)
        st.metric("Success Rate", f"{success_rate:.1f}%")
    with col3:
        st.metric("Total Words", f"{summary.get('total_words', 0):,}")
    with col4:
        avg_time = summary.get('avg_time_ms', 0)
        st.metric("Avg Time", f"{avg_time}ms" if avg_time > 0 else "N/A")
    
    st.divider()
    
    st.markdown("### Method Overview")
    
    method_stats = container.stats_repo.get_method_stats(days)
    method_comparison = container.stats_repo.get_method_comparison(days)
    
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        with card_container(key="analytics_method_pie"):
            st.markdown('<div class="section-header">Method Distribution</div>', unsafe_allow_html=True)
            fig = create_method_pie_chart(method_stats)
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        with card_container(key="analytics_radar"):
            st.markdown('<div class="section-header">Method Comparison</div>', unsafe_allow_html=True)
            if method_comparison:
                fig = create_method_radar_chart(method_comparison)
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("No data available for comparison")
    
    with col3:
        with card_container(key="analytics_efficiency"):
            st.markdown('<div class="section-header">Efficiency Rankings</div>', unsafe_allow_html=True)
            
            if method_stats:
                ranked = sorted(
                    method_stats.items(),
                    key=lambda x: x[1].get('efficiency_score', 0),
                    reverse=True
                )
                
                for rank, (method, data) in enumerate(ranked, 1):
                    attempts = data.get('total_attempts', 0)
                    if attempts == 0:
                        continue
                    
                    efficiency = data.get('efficiency_score', 0)
                    success_rate = data.get('success_rate', 0)
                    avg_time = data.get('avg_time_ms', 0)
                    
                    c1, c2, c3 = st.columns([3, 2, 2])
                    with c1:
                        medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"{rank}."))
                        st.markdown(f"**{medal} {METHOD_LABELS.get(method, method)}**")
                    with c2:
                        st.caption(f"Efficiency: **{efficiency}**")
                    with c3:
                        st.caption(f"SR: {success_rate:.0f}% | {avg_time}ms")
            else:
                st.info("No method data available")
    
    st.divider()
    
    st.markdown("### Activity Trends")
    
    timeline_days = days if days and days <= 30 else 30
    method_timeline = container.stats_repo.get_method_timeline(timeline_days)
    daily_activity = container.stats_repo.get_daily_activity(timeline_days)
    
    col1, col2 = st.columns(2)
    
    with col1:
        with card_container(key="analytics_timeline"):
            st.markdown('<div class="section-header">Daily Activity</div>', unsafe_allow_html=True)
            fig = create_activity_timeline(daily_activity)
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        with card_container(key="analytics_stacked"):
            st.markdown('<div class="section-header">Method Usage Over Time</div>', unsafe_allow_html=True)
            fig = create_method_timeline_stacked(method_timeline)
            st.plotly_chart(fig, width="stretch")
    
    st.divider()
    
    st.markdown("### Success & Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with card_container(key="analytics_success_fail"):
            st.markdown('<div class="section-header">Success/Fail by Method</div>', unsafe_allow_html=True)
            fig = create_success_fail_ratio_chart(method_stats)
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        with card_container(key="analytics_avg_time"):
            st.markdown('<div class="section-header">Avg Extraction Time</div>', unsafe_allow_html=True)
            fig = create_avg_time_comparison_chart(method_stats)
            st.plotly_chart(fig, width="stretch")
    
    st.divider()
    
    st.markdown("### Domain & Error Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with card_container(key="analytics_domains"):
            st.markdown('<div class="section-header">Top Domains</div>', unsafe_allow_html=True)
            domain_stats = container.stats_repo.get_domain_stats(10)
            fig = create_domain_bar_chart(domain_stats, limit=8)
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        with card_container(key="analytics_errors"):
            st.markdown('<div class="section-header">Error Distribution</div>', unsafe_allow_html=True)
            error_analysis = container.stats_repo.get_error_analysis(days)
            fig = create_error_pie_chart(error_analysis)
            st.plotly_chart(fig, width="stretch")
            
            error_domains = error_analysis.get('by_domain', {})
            if error_domains:
                st.caption("**Top error domains:**")
                for domain, count in list(error_domains.items())[:3]:
                    st.caption(f"• {domain}: {count} errors")
    
    st.divider()
    
    st.markdown("### Recent Activity")
    
    with card_container(key="analytics_recent"):
        recent = container.stats_repo.get_recent(15)
        
        if recent:
            for item in recent:
                status_icon = "✓" if item.success else "✗"
                status_color = "#299c46" if item.success else "#c4172c"
                method = item.method or 'unknown'
                time_str = f"{item.time_ms}ms"
                url = item.url or ''
                word_count = item.word_count or 0
                
                method_label = METHOD_LABELS.get(method, method)
                
                c1, c2, c3 = st.columns([5, 2, 2])
                with c1:
                    st.caption(f"<span style='color:{status_color}'>{status_icon}</span> {url[:50]}{'...' if len(url) > 50 else ''}", unsafe_allow_html=True)
                with c2:
                    st.caption(f"`{method_label}`")
                with c3:
                    st.caption(f"{time_str} | {word_count:,} words")
        else:
            st.info("No recent activity. Start scraping to see results here.")
