import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from app.container import container


def render():
    st.header("⚙️ Settings")
    
    with st.expander("🎨 Appearance", expanded=True):
        current_theme = container.state_repo.get_setting('theme', 'dark')
        theme = st.radio(
            "Theme",
            ["dark", "light"],
            index=0 if current_theme == "dark" else 1
        )
        
        if theme != current_theme:
            container.state_repo.set_setting('theme', theme)
            st.session_state.theme = theme
            st.rerun()
    
    with st.expander("📤 Export Settings"):
        st.markdown("**Export format for normal links**")
        
        export_format = st.selectbox(
            "Default Format",
            ["md", "txt", "json"],
            index=0 if container.state_repo.get_setting('export_format') == 'md' else 
                  1 if container.state_repo.get_setting('export_format') == 'txt' else 2
        )
        
        if export_format != container.state_repo.get_setting('export_format'):
            container.state_repo.set_setting('export_format', export_format)
            st.success(f"Export format set to: {export_format.upper()}")
    
    with st.expander("🤖 Scraping Behavior"):
        respect_robots = st.checkbox(
            "Respect robots.txt",
            value=bool(container.state_repo.get_setting('respect_robots_txt', True))
        )
        if respect_robots != container.state_repo.get_setting('respect_robots_txt'):
            container.state_repo.set_setting('respect_robots_txt', respect_robots)
            st.success("Updated robots.txt setting")
        
        concurrent_jobs = st.slider(
            "Concurrent Jobs",
            min_value=1,
            max_value=5,
            value=container.state_repo.get_setting('concurrent_jobs', 3)
        )
        if concurrent_jobs != container.state_repo.get_setting('concurrent_jobs'):
            container.state_repo.set_setting('concurrent_jobs', concurrent_jobs)
        
        retry_count = st.slider(
            "Retry Failed",
            min_value=0,
            max_value=3,
            value=container.state_repo.get_setting('retry_count', 2)
        )
        if retry_count != container.state_repo.get_setting('retry_count'):
            container.state_repo.set_setting('retry_count', retry_count)
    
    with st.expander("📚 Novel Settings"):
        st.markdown("**Delay between chapters (to avoid IP blocking)**")
        col1, col2 = st.columns(2)
        with col1:
            novel_delay_min = st.number_input(
                "Min Delay (seconds)",
                min_value=30, max_value=180,
                value=container.state_repo.get_setting('novel_delay_min', 90)
            )
        with col2:
            novel_delay_max = st.number_input(
                "Max Delay (seconds)",
                min_value=60, max_value=300,
                value=container.state_repo.get_setting('novel_delay_max', 120)
            )
        
        if novel_delay_min != container.state_repo.get_setting('novel_delay_min'):
            container.state_repo.set_setting('novel_delay_min', novel_delay_min)
        if novel_delay_max != container.state_repo.get_setting('novel_delay_max'):
            container.state_repo.set_setting('novel_delay_max', novel_delay_max)
        
        st.caption(f"Current: {container.state_repo.get_setting('novel_delay_min', 90)}-{container.state_repo.get_setting('novel_delay_max', 120)} seconds")
    
    with st.expander("💾 Data Management"):
        auto_save = st.checkbox(
            "Auto-save queue on close",
            value=bool(container.state_repo.get_setting('auto_save_queue', True))
        )
        if auto_save != container.state_repo.get_setting('auto_save_queue'):
            container.state_repo.set_setting('auto_save_queue', auto_save)
        
        if st.button("🗑️ Clear All Settings"):
            container.state_repo.reset_settings()
            st.success("Settings reset to defaults")
            st.rerun()
    
    st.divider()
    
    with st.expander("🔑 API Configuration"):
        st.markdown("**WebScrapingAPI Key**")
        
        import os
        from dotenv import load_dotenv
        from pathlib import Path
        
        load_dotenv(Path(__file__).parent.parent.parent / ".env")
        current_key = os.getenv("WEBSCRAPING_API_KEY", "")
        
        masked_key = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "(not set)"
        st.text_input("Current Key", value=masked_key, disabled=True)
        
        new_key = st.text_input(
            "New API Key",
            value="",
            type="password",
            help="Enter your WebScrapingAPI key"
        )
        
        if new_key and new_key != current_key:
            env_path = Path(__file__).parent.parent.parent / ".env"
            with open(env_path, "w") as f:
                f.write(f"WEBSCRAPING_API_KEY={new_key}\n")
            st.success("API key saved to .env! Restart the app to apply changes.")
    
    st.divider()
    
    st.markdown("### Current Settings")
    st.json(container.state_repo.get_all_settings())
