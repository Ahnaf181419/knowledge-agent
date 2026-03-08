import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from app.container import container
from app.logger import logger
from utils.validators import is_valid_url, validate_chapter_range, parse_tags
from scraper.router import route_url


def render():
    col_main, col_side = st.columns([3, 1])
    
    with col_main:
        render_input_section()
        render_queue_section()
    
    with col_side:
        render_quick_actions()
        render_stats_panel()


def render_input_section():
    st.markdown("### Add URLs")
    
    tab1, tab2 = st.tabs(["Normal Links", "Novel Links"])
    
    with tab1:
        render_normal_input()
    
    with tab2:
        render_novel_input()


def render_normal_input():
    normal_urls = st.text_area(
        "Paste URLs (one per line)",
        height=120,
        placeholder="https://en.wikipedia.org/wiki/Mars\nhttps://medium.com/my-article",
        key="normal_urls_input"
    )
    
    col1, col2 = st.columns([2, 1])
    with col1:
        tags_input = st.text_input(
            "Tags (comma separated)",
            placeholder="AI, technology, science",
            key="tags_input"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add URLs", type="primary", width="stretch", key="add_normal_btn"):
            add_normal_urls(normal_urls, tags_input)
    
    if normal_urls.strip():
        render_url_preview(normal_urls)


def render_url_preview(urls_text: str):
    urls = [u.strip() for u in urls_text.split('\n') if u.strip()][:5]
    if not urls:
        return
    
    st.markdown("<div class='url-preview'>", unsafe_allow_html=True)
    st.markdown("**Preview:**")
    
    for url in urls:
        route = route_url(url)
        valid = is_valid_url(url)
        
        type_class = {"normal": "type-normal", "novel": "type-novel", "heavy": "type-heavy"}.get(route, "type-normal")
        type_icon = {"normal": "article", "novel": "book", "heavy": "flash_on", "skip": "block"}.get(route, "article")
        
        status_text = "Valid" if valid else "Invalid"
        status_color = "#4CAF50" if valid else "#F44336"
        
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 8px; margin: 4px 0;">
            <span class="type-badge {type_class}">{route}</span>
            <span style="font-size: 12px; color: #666; flex: 1; overflow: hidden; text-overflow: ellipsis;">{url[:60]}{'...' if len(url) > 60 else ''}</span>
            <span style="font-size: 11px; color: {status_color};">{status_text}</span>
        </div>
        """, unsafe_allow_html=True)
    
    if len(urls_text.split('\n')) > 5:
        st.caption(f"... and {len(urls_text.split('\n')) - 5} more")
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_novel_input():
    novel_url = st.text_input(
        "Novel URL",
        placeholder="",
        key="novel_url_input"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        start_chapter = st.number_input("Start Chapter", min_value=1, value=1, key="start_ch")
    with col2:
        end_chapter = st.number_input("End Chapter", min_value=1, value=10, key="end_ch")
    
    if novel_url.strip():
        render_novel_preview(novel_url, start_chapter, end_chapter)
    
    if st.button("Add Novel", type="primary", width="stretch", key="add_novel_btn"):
        add_novel(novel_url, start_chapter, end_chapter)


def render_novel_preview(url: str, start: int, end: int):
    st.markdown("<div class='url-preview'>", unsafe_allow_html=True)
    
    if not is_valid_url(url):
        st.markdown("<span style='color: #F44336;'>Invalid URL format</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    existing_chapters = container.history_repo.get_novel_chapters(url)
    requested = set(range(start, end + 1))
    new_chapters = requested - set(existing_chapters)
    already_done = requested & set(existing_chapters)
    
    total = end - start + 1
    eta_minutes = len(new_chapters) * 2
    
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
        <span><strong>Total chapters:</strong> {total}</span>
        <span class="eta-badge">~{eta_minutes} min estimated</span>
    </div>
    """, unsafe_allow_html=True)
    
    if already_done:
        st.info(f"Chapters {sorted(already_done)[:5]}{'...' if len(already_done) > 5 else ''} already extracted")
    
    if new_chapters:
        st.success(f"Will extract: {len(new_chapters)} new chapters ({min(new_chapters)}-{max(new_chapters)})")
    elif not already_done:
        st.warning("No new chapters to extract")
    
    if existing_chapters and len(existing_chapters) <= 50:
        render_chapter_grid(existing_chapters, start, end)
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_chapter_grid(existing: list, start: int, end: int):
    st.markdown("**Chapter Status:**")
    st.markdown("<div class='chapter-grid'>", unsafe_allow_html=True)
    
    for ch in range(start, min(end + 1, start + 50)):
        if ch in existing:
            cell_class = "chapter-done"
        else:
            cell_class = "chapter-pending"
        st.markdown(f"<div class='chapter-cell {cell_class}'>{ch}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("Green = extracted, Gray = pending")


def render_queue_section():
    st.divider()
    st.markdown("### Queue")
    
    queue = container.state_repo.queue
    urls = queue.get('urls', [])
    novels = queue.get('novels', [])
    
    if not urls and not novels:
        render_empty_state()
        return
    
    pending = [u for u in urls if u.get('status') == 'pending']
    completed = [u for u in urls if u.get('status') == 'completed']
    failed = [u for u in urls if u.get('status') == 'failed']
    
    render_filter_tabs(len(pending), len(completed), len(failed), len(novels))
    
    filter_state = st.session_state.get('queue_filter', 'all')
    
    if filter_state == 'pending':
        display_urls = pending
    elif filter_state == 'completed':
        display_urls = completed
    elif filter_state == 'failed':
        display_urls = failed
    else:
        display_urls = urls
    
    if display_urls:
        render_url_cards(display_urls)
    
    if novels and filter_state in ['all', 'novels']:
        render_novel_cards(novels)
    
    render_bulk_actions(len(pending), len(failed))


def render_empty_state():
    st.markdown("""
    <div class="empty-state">
        <div class="icon">inbox</div>
        <h4>No URLs in queue</h4>
        <p>Add some URLs above to get started</p>
    </div>
    """, unsafe_allow_html=True)


def render_filter_tabs(pending: int, completed: int, failed: int, novels: int):
    if 'queue_filter' not in st.session_state:
        st.session_state.queue_filter = 'all'
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    
    with col1:
        if st.button(f"All ({len(container.state_repo.queue.get('urls', []))})", key="filter_all"):
            st.session_state.queue_filter = 'all'
            st.rerun()
    
    with col2:
        if st.button(f"Pending ({pending})", key="filter_pending"):
            st.session_state.queue_filter = 'pending'
            st.rerun()
    
    with col3:
        if st.button(f"Done ({completed})", key="filter_completed"):
            st.session_state.queue_filter = 'completed'
            st.rerun()
    
    with col4:
        if st.button(f"Failed ({failed})", key="filter_failed"):
            st.session_state.queue_filter = 'failed'
            st.rerun()


def render_url_cards(urls: list):
    for i, entry in enumerate(urls):
        status = entry.get('status', 'pending')
        url = entry.get('url', '')
        route = route_url(url)
        
        badge_class = f"badge-{status}"
        type_class = {"normal": "type-normal", "novel": "type-novel", "heavy": "type-heavy", "skip": "type-normal"}.get(route, "type-normal")
        
        status_icon = {"pending": "schedule", "completed": "check_circle", "failed": "error", "processing": "sync"}.get(status, "schedule")
        
        st.markdown(f"""
        <div class="url-card {status}">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span class="type-badge {type_class}">{route}</span>
                <code style="flex: 1; font-size: 12px; background: transparent;">{url[:70]}{'...' if len(url) > 70 else ''}</code>
                <span class="status-badge {badge_class}">{status_icon} {status}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            if entry.get('tags'):
                st.caption(f"Tags: {', '.join(entry['tags'][:3])}")
        with col2:
            if entry.get('error'):
                st.caption(f"Error: {entry['error'][:30]}...")
        with col3:
            if st.button("Remove", key=f"del_{i}_{url[:20]}", type="secondary"):
                container.state_repo.remove_url(url)
                st.rerun()


def render_novel_cards(novels: list):
    st.markdown("**Novels:**")
    
    for i, entry in enumerate(novels):
        status = entry.get('status', 'pending')
        url = entry.get('url', '')
        novel_name = url.split('/')[-1]
        
        badge_class = f"badge-{status}"
        ch_range = f"Ch {entry['start_chapter']}-{entry['end_chapter']}"
        total_ch = entry['end_chapter'] - entry['start_chapter'] + 1
        eta = total_ch * 2
        
        st.markdown(f"""
        <div class="url-card {status}">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span class="type-badge type-novel">novel</span>
                <div style="flex: 1;">
                    <div style="font-weight: 500;">{novel_name[:40]}</div>
                    <div style="font-size: 11px; color: #666;">{ch_range} ({total_ch} chapters) - ~{eta} min</div>
                </div>
                <span class="status-badge {badge_class}">{status}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Remove", key=f"del_novel_{i}", type="secondary"):
            container.state_repo.remove_novel(url)
            st.rerun()


def render_bulk_actions(pending_count: int, failed_count: int):
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Start Scraping", type="primary", width="stretch", disabled=pending_count == 0):
            start_scraping()
    
    with col2:
        if st.button("Retry Failed", width="stretch", disabled=failed_count == 0):
            retry_failed()
    
    with col3:
        if st.button("Clear Completed", width="stretch"):
            container.state_repo.clear_completed()
            show_toast("Cleared completed items", "success")
            st.rerun()
    
    with col4:
        if st.button("Clear All", width="stretch", type="secondary"):
            container.state_repo.queue['urls'] = []
            container.state_repo.queue['novels'] = []
            container.state_repo.save_queue()
            show_toast("Queue cleared", "info")
            st.rerun()


def render_quick_actions():
    st.markdown("### Quick Actions")
    
    if st.button("Scrape Wikipedia Article", width="stretch", key="quick_wiki"):
        st.session_state.normal_urls_input = "https://en.wikipedia.org/wiki/"
    
    if st.button("Add Novel from Clipboard", width="stretch", key="quick_novel"):
        st.info("Paste novel URL in the input field")
    
    st.divider()
    
    render_api_status()


def render_api_status():
    try:
        from app.api_tracker import get_api_usage, get_next_reset_date
        usage = get_api_usage()
        
        st.markdown("**API Status:**")
        
        percentage = usage['percentage']
        bar_color = "#4CAF50" if percentage < 70 else "#FF9800" if percentage < 90 else "#F44336"
        
        st.markdown(f"""
        <div style="margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; font-size: 12px;">
                <span>{usage['calls_used']:,} / {usage['calls_limit']:,}</span>
                <span>{percentage}%</span>
            </div>
            <div style="height: 6px; background: #e0e0e0; border-radius: 3px; margin-top: 4px;">
                <div style="height: 100%; width: {percentage}%; background: {bar_color}; border-radius: 3px;"></div>
            </div>
        </div>
        <div style="font-size: 11px; color: #666;">Resets: {get_next_reset_date()}</div>
        """, unsafe_allow_html=True)
    except:
        pass


def render_stats_panel():
    st.divider()
    st.markdown("### Statistics")
    
    try:
        stats = container.history_repo.get_stats()
        
        st.metric("Total Extracted", stats.get('normal_links', 0))
        st.metric("Novels", stats.get('novels', 0))
        st.metric("Chapters", stats.get('total_chapters', 0))
        st.metric("Total Words", f"{stats.get('total_words', 0):,}")
    except:
        pass


def show_toast(message: str, toast_type: str = "info"):
    st.markdown(f"""
    <div class="toast toast-{toast_type}">{message}</div>
    <script>
        setTimeout(function() {{
            document.querySelector('.toast').style.display = 'none';
        }}, 3000);
    </script>
    """, unsafe_allow_html=True)


def add_normal_urls(urls_text: str, tags_input: str):
    if not urls_text.strip():
        st.error("Please enter at least one URL")
        return
    
    tags = parse_tags(tags_input)
    urls = [u.strip() for u in urls_text.split('\n') if u.strip()]
    
    added = 0
    already_extracted = 0
    in_queue = 0
    invalid = 0
    
    for url in urls:
        if not is_valid_url(url):
            invalid += 1
            continue
        
        route = route_url(url)
        if route == "skip":
            invalid += 1
            continue
        
        if container.history_repo.is_extracted(url):
            already_extracted += 1
            continue
        
        if container.state_repo.url_in_queue(url):
            in_queue += 1
            continue
        
        if container.state_repo.add_url(url, "normal", tags):
            added += 1
    
    messages = []
    if added > 0:
        messages.append(f"Added {added} URL(s)")
    if already_extracted > 0:
        messages.append(f"Skipped {already_extracted} already extracted")
    if in_queue > 0:
        messages.append(f"Skipped {in_queue} in queue")
    if invalid > 0:
        messages.append(f"Skipped {invalid} invalid")
    
    if added > 0:
        show_toast(" + ".join(messages), "success")
    else:
        show_toast(" + ".join(messages), "info")
    
    st.rerun()


def add_novel(url: str, start: int, end: int):
    if not url.strip():
        st.error("Please enter a novel URL")
        return
    
    if not is_valid_url(url):
        st.error("Invalid URL format")
        return
    
    valid, msg = validate_chapter_range(start, end)
    if not valid:
        st.error(msg)
        return
    
    existing_chapters = container.history_repo.get_novel_chapters(url)
    requested = set(range(start, end + 1))
    new_chapters = requested - set(existing_chapters)
    
    if not new_chapters:
        show_toast("All chapters already extracted", "info")
        return
    
    if container.state_repo.novel_in_queue(url):
        show_toast("Novel already in queue", "warning")
        return
    
    if container.state_repo.add_novel(url, min(new_chapters), max(new_chapters)):
        show_toast(f"Added novel: Chapters {min(new_chapters)}-{max(new_chapters)}", "success")
        st.rerun()


def start_scraping():
    queue = container.state_repo.queue
    urls = [u for u in queue.get('urls', []) if u.get('status') == 'pending']
    novels = [n for n in queue.get('novels', []) if n.get('status') == 'pending']
    
    if not urls and not novels:
        show_toast("No pending URLs to scrape", "warning")
        return
    
    progress_container = st.empty()
    
    if urls:
        total = len(urls)
        progress_container.markdown(f"""
        <div class="progress-container">
            <div class="progress-header">
                <span><strong>Scraping Progress</strong></span>
                <span>0/{total}</span>
            </div>
            <div class="progress-bar-animated">
                <div class="progress-fill-animated" style="width: 0%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        for i, entry in enumerate(urls):
            container.state_repo.update_url_status(entry['url'], 'processing')
            
            try:
                from scraper.runner import run_scraper
                results = run_scraper([entry])
                
                for result in results:
                    container.state_repo.update_url_status(result['url'], result['status'])
            except Exception as e:
                logger.error(f"Scraping error: {str(e)}")
                container.state_repo.update_url_status(entry['url'], 'failed')
            
            pct = int((i + 1) / total * 100)
            progress_container.markdown(f"""
            <div class="progress-container">
                <div class="progress-header">
                    <span><strong>Scraping Progress</strong></span>
                    <span>{i + 1}/{total}</span>
                </div>
                <div class="progress-bar-animated">
                    <div class="progress-fill-animated" style="width: {pct}%"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    if novels:
        from scraper.novel_scraper import NovelScraper
        
        for entry in novels:
            container.state_repo.update_novel_status(entry['url'], 'processing')
            novel_name = entry['url'].split('/')[-1]
            
            def progress_callback(current, total):
                pct = int(current / total * 100)
                progress_container.markdown(f"""
                <div class="progress-container">
                    <div class="progress-header">
                        <span><strong>Novel: {novel_name[:30]}</strong></span>
                        <span>Chapter {current}/{total}</span>
                    </div>
                    <div class="progress-bar-animated">
                        <div class="progress-fill-animated" style="width: {pct}%"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            try:
                with NovelScraper(
                    delay_min=int(container.state_repo.get_setting('novel_delay_min', 90) or 90),
                    delay_max=int(container.state_repo.get_setting('novel_delay_max', 120) or 120),
                    retry_count=int(container.state_repo.get_setting('retry_count', 2) or 2)
                ) as scraper:
                    result = scraper.scrape_novel(
                        novel_url=entry['url'],
                        novel_name=novel_name,
                        start_chapter=entry['start_chapter'],
                        end_chapter=entry['end_chapter'],
                        force=False,
                        progress_callback=progress_callback
                    )
                
                for ch_result in result.get('results', []):
                    if ch_result['status'] == 'failed':
                        container.state_repo.add_to_retry_novel(
                            entry['url'],
                            ch_result['chapter'],
                            ch_result.get('error', 'Unknown error')
                        )
                
                if result['success'] > 0:
                    container.state_repo.update_novel_status(entry['url'], 'completed')
                else:
                    container.state_repo.update_novel_status(entry['url'], 'failed')
                    
            except Exception as e:
                logger.error(f"Novel scraping error: {str(e)}")
                container.state_repo.update_novel_status(entry['url'], 'failed')
    
    progress_container.empty()
    show_toast("Scraping completed!", "success")
    st.rerun()


def retry_failed():
    failed_urls = [u for u in container.state_repo.queue.get('urls', []) if u.get('status') == 'failed']
    
    if not failed_urls:
        show_toast("No failed URLs to retry", "info")
        return
    
    for entry in failed_urls:
        container.state_repo.update_url_status(entry['url'], 'pending')
    
    show_toast(f"Reset {len(failed_urls)} failed URLs to pending", "success")
    st.rerun()
