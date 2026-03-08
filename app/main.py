"""
KnowledgeAgent - Main Application Entry Point

Uses st.tabs() for horizontal top navigation.
Single-page app with tab-based navigation.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from app.styles import apply_custom_styles
from app.container import container

if 'theme' not in st.session_state:
    st.session_state.theme = container.state_repo.get_setting('theme', 'dark')

st.set_page_config(
    page_title="KnowledgeAgent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_custom_styles()

current_theme = st.session_state.get('theme', 'dark')
icon = "🌙" if current_theme == "dark" else "☀️"

query_params = st.query_params
if "theme" in query_params:
    new_theme = query_params["theme"]
    if new_theme in ["light", "dark"]:
        st.session_state.theme = new_theme
        container.state_repo.set_setting('theme', new_theme)
        del query_params["theme"]
    st.rerun()

st.markdown(f"""
<div class="top-nav" style="display: flex; align-items: center; justify-content: space-between; padding: 12px 24px; margin: -12px -24px 20px -24px; border-bottom: 1px solid var(--border-color);">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 24px;">🧠</span>
        <span style="font-size: 20px; font-weight: 600; color: var(--accent-color);">KnowledgeAgent</span>
    </div>
    <div style="display: flex; align-items: center; gap: 16px;">
        <a href="/?theme={'light' if current_theme == 'dark' else 'dark'}" style="background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 18px; text-decoration: none; display: inline-block;">{icon}</a>
    </div>
</div>
""", unsafe_allow_html=True)

tab_dashboard, tab_add, tab_queue, tab_results, tab_analytics, tab_settings = st.tabs([
    "📊 Dashboard",
    "➕ Add Links",
    "📋 Queue", 
    "📁 Results",
    "📈 Analytics",
    "⚙️ Settings"
])

with tab_dashboard:
    from app.pages.dashboard import render as render_dashboard
    render_dashboard()

with tab_add:
    from app.pages.home import render as render_add_urls
    render_add_urls()

with tab_queue:
    from app.pages.queue import render as render_queue
    render_queue()

with tab_results:
    from app.pages.results import render as render_results
    render_results()

with tab_analytics:
    from app.pages.analytics import render as render_analytics
    render_analytics()

with tab_settings:
    from app.pages.settings import render as render_settings
    render_settings()
