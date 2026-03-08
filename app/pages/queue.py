"""
Queue Page with Retry Tab
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from app.container import container


def render():
    st.header("Queue Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Pending URLs", "Pending Novels", "Retry (Normal)", "Retry (Novel)"])
    
    with tab1:
        render_pending_urls()
    
    with tab2:
        render_pending_novels()
    
    with tab3:
        render_retry_normal()
    
    with tab4:
        render_retry_novel()


def render_pending_urls():
    """Render pending normal URLs"""
    queue = container.state_repo.queue
    urls = [u for u in queue.get('urls', []) if u.get('status') == 'pending']
    completed = [u for u in queue.get('urls', []) if u.get('status') == 'completed']
    failed = [u for u in queue.get('urls', []) if u.get('status') == 'failed']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending", len(urls))
    with col2:
        st.metric("Completed", len(completed))
    with col3:
        st.metric("Failed", len(failed))
    
    if not urls:
        st.info("No pending URLs")
        return
    
    st.subheader(f"Pending URLs ({len(urls)})")
    for i, entry in enumerate(urls):
        cols = st.columns([4, 1, 1, 1])
        with cols[0]:
            st.code(entry['url'], language=None)
        with cols[1]:
            route = entry.get('type', 'normal')
            st.caption(f"Type: {route}")
        with cols[2]:
            tags = entry.get('tags', [])
            if tags:
                st.caption(f"Tags: {', '.join(tags[:2])}")
        with cols[3]:
            if st.button("X", key=f"del_url_{i}"):
                container.state_repo.remove_url(entry['url'])
                st.rerun()


def render_pending_novels():
    """Render pending novels"""
    queue = container.state_repo.queue
    novels = [n for n in queue.get('novels', []) if n.get('status') == 'pending']
    
    if not novels:
        st.info("No pending novels")
        return
    
    st.subheader(f"Pending Novels ({len(novels)})")
    for i, entry in enumerate(novels):
        cols = st.columns([4, 1, 1, 1])
        with cols[0]:
            st.code(entry['url'], language=None)
        with cols[1]:
            ch_range = f"Ch {entry['start_chapter']}-{entry['end_chapter']}"
            st.caption(ch_range)
        with cols[2]:
            chapters = entry['end_chapter'] - entry['start_chapter'] + 1
            st.caption(f"Chapters: {chapters}")
        with cols[3]:
            if st.button("X", key=f"del_novel_{i}"):
                container.state_repo.remove_novel(entry['url'])
                st.rerun()


def render_retry_normal():
    """Render retry queue for normal links with batch operations"""
    retry_list = container.state_repo.get_retry_normal()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.subheader(f"Retry Queue ({len(retry_list)})")
    with col2:
        if st.button("🔄 Retry All", key="retry_all_normal", disabled=len(retry_list) == 0, use_container_width=True):
            retry_all_normal()
    with col3:
        if st.button("🗑️ Clear All", key="clear_all_normal", disabled=len(retry_list) == 0, use_container_width=True):
            container.state_repo.queue['retry_normal'] = []
            container.state_repo.save_queue()
            st.rerun()
    
    if not retry_list:
        st.info("No failed URLs to retry")
        return
    
    for i, entry in enumerate(retry_list):
        cols = st.columns([4, 2, 1, 1])
        with cols[0]:
            st.code(entry.url, language=None)
        with cols[1]:
            error_msg = entry.error or 'Unknown'
            st.caption(f"Error: {error_msg[:40]}{'...' if len(error_msg) > 40 else ''}")
        with cols[2]:
            if st.button("API Retry", key=f"retry_normal_{i}"):
                retry_with_api_normal(entry.url, list(entry.tags or []))
                st.rerun()
        with cols[3]:
            if st.button("X", key=f"remove_normal_{i}"):
                container.state_repo.remove_from_retry_normal(entry.url)
                st.rerun()


def render_retry_novel():
    """Render retry queue for novel chapters with batch operations"""
    retry_list = container.state_repo.get_retry_novel()
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.subheader(f"Retry Queue ({len(retry_list)})")
    with col2:
        if st.button("🔄 Retry All", key="retry_all_novel", disabled=len(retry_list) == 0, use_container_width=True):
            retry_all_novel()
    with col3:
        if st.button("🗑️ Clear All", key="clear_all_novel", disabled=len(retry_list) == 0, use_container_width=True):
            container.state_repo.queue['retry_novel'] = []
            container.state_repo.save_queue()
            st.rerun()
    
    if not retry_list:
        st.info("No failed novel chapters to retry")
        return
    
    for i, entry in enumerate(retry_list):
        cols = st.columns([4, 1, 1, 1, 1])
        with cols[0]:
            st.code(entry.url, language=None)
        with cols[1]:
            st.caption(f"Ch. {entry.chapter or 'N/A'}")
        with cols[2]:
            error_msg = entry.error or 'Unknown'
            display_error = error_msg[:20] + "..." if len(error_msg) > 20 else error_msg
            st.caption(f"Error: {display_error}")
        with cols[3]:
            if st.button("API Retry", key=f"retry_novel_{i}"):
                retry_with_api_novel(entry.url, entry.chapter or 1)
                st.rerun()
        with cols[4]:
            if st.button("X", key=f"remove_novel_{i}"):
                container.state_repo.remove_from_retry_novel(entry.url, entry.chapter or 1)
                st.rerun()


def retry_all_normal():
    """Retry all normal URLs in retry queue"""
    retry_list = container.state_repo.get_retry_normal()
    success_count = 0
    
    progress_bar = st.progress(len(retry_list))
    
    for i, entry in enumerate(retry_list):
        result = retry_with_api_normal_silent(entry.url, list(entry.tags or []))
        if result:
            success_count += 1
        progress_bar.progress(i + 1)
    
    st.success(f"Retried {len(retry_list)} URLs. Success: {success_count}")
    st.rerun()


def retry_all_novel():
    """Retry all novel chapters in retry queue"""
    retry_list = container.state_repo.get_retry_novel()
    success_count = 0
    
    progress_bar = st.progress(len(retry_list))
    
    for i, entry in enumerate(retry_list):
        result = retry_with_api_novel_silent(entry.url, entry.chapter or 1)
        if result:
            success_count += 1
        progress_bar.progress(i + 1)
    
    st.success(f"Retried {len(retry_list)} chapters. Success: {success_count}")
    st.rerun()


def retry_with_api_normal(url: str, tags: list):
    """Retry normal URL with WebScrapingAPI"""
    try:
        from scraper.engines.webscrapingapi_engine import WebScrapingAPIEngine
        from scraper.extractors.text_extractor import TextExtractor
        from storage.folder_manager import get_normal_folder
        from storage.markdown_saver import save_normal_article
        
        engine = WebScrapingAPIEngine()
        html_content = engine.scrape(url)
        
        if html_content:
            text_content = TextExtractor.extract_from_html(html_content, 'md')
            if text_content:
                folder = get_normal_folder(url)
                word_count = len(text_content.split())
                
                file_path = save_normal_article(
                    folder=folder,
                    url=url,
                    title=url.split('/')[-1][:50],
                    content=text_content,
                    tags=tags,
                    word_count=word_count,
                    output_format='md'
                )
                
                st.success(f"Saved {word_count} words")
                container.state_repo.remove_from_retry_normal(url)
                return True
        
        st.error("WebScrapingAPI failed")
        return False
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False


def retry_with_api_novel(url: str, chapter: int):
    """Retry novel chapter with WebScrapingAPI"""
    try:
        from scraper.engines.webscrapingapi_engine import WebScrapingAPIEngine
        from scraper.extractors.text_extractor import TextExtractor
        from storage.folder_manager import get_novel_folder
        from storage.markdown_saver import save_chapter
        
        chapter_url = f"{url}/chapter-{chapter}?service=web"
        engine = WebScrapingAPIEngine()
        html_content = engine.scrape(chapter_url)
        
        if html_content:
            text_content = TextExtractor.extract_from_html(html_content, 'md')
            if text_content:
                folder = get_novel_folder(url)
                word_count = len(text_content.split())
                
                novel_name = url.split('/')[-1]
                
                metadata = container.history_repo.get_novel_metadata(url) or {}
                genre = metadata.get("genre", [])
                tags = metadata.get("tags", [])
                
                save_chapter(
                    folder=folder,
                    chapter_number=chapter,
                    title=f"Chapter {chapter}",
                    text=text_content,
                    word_count=word_count,
                    source_url=chapter_url,
                    novel_name=novel_name,
                    genre=genre,
                    tags=tags
                )
                
                st.success(f"Saved {word_count} words")
                container.state_repo.remove_from_retry_novel(url, chapter)
                return True
        
        st.error("WebScrapingAPI failed")
        return False
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False


def retry_with_api_normal_silent(url: str, tags: list) -> bool:
    """Retry normal URL without UI feedback (for batch operations)"""
    try:
        from scraper.engines.webscrapingapi_engine import WebScrapingAPIEngine
        from scraper.extractors.text_extractor import TextExtractor
        from storage.folder_manager import get_normal_folder
        from storage.markdown_saver import save_normal_article
        
        engine = WebScrapingAPIEngine()
        html_content = engine.scrape(url)
        
        if html_content:
            text_content = TextExtractor.extract_from_html(html_content, 'md')
            if text_content:
                folder = get_normal_folder(url)
                word_count = len(text_content.split())
                
                file_path = save_normal_article(
                    folder=folder,
                    url=url,
                    title=url.split('/')[-1][:50],
                    content=text_content,
                    tags=tags,
                    word_count=word_count,
                    output_format='md'
                )
                
                container.state_repo.remove_from_retry_normal(url)
                return True
        
        return False
        
    except:
        return False


def retry_with_api_novel_silent(url: str, chapter: int) -> bool:
    """Retry novel chapter without UI feedback (for batch operations)"""
    try:
        from scraper.engines.webscrapingapi_engine import WebScrapingAPIEngine
        from scraper.extractors.text_extractor import TextExtractor
        from storage.folder_manager import get_novel_folder
        from storage.markdown_saver import save_chapter
        
        chapter_url = f"{url}/chapter-{chapter}?service=web"
        engine = WebScrapingAPIEngine()
        html_content = engine.scrape(chapter_url)
        
        if html_content:
            text_content = TextExtractor.extract_from_html(html_content, 'md')
            if text_content:
                folder = get_novel_folder(url)
                word_count = len(text_content.split())
                
                novel_name = url.split('/')[-1]
                
                metadata = container.history_repo.get_novel_metadata(url) or {}
                genre = metadata.get("genre", [])
                tags = metadata.get("tags", [])
                
                save_chapter(
                    folder=folder,
                    chapter_number=chapter,
                    title=f"Chapter {chapter}",
                    text=text_content,
                    word_count=word_count,
                    source_url=chapter_url,
                    novel_name=novel_name,
                    genre=genre,
                    tags=tags
                )
                
                container.state_repo.remove_from_retry_novel(url, chapter)
                return True
        
        return False
        
    except:
        return False
