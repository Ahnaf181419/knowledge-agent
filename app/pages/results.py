import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from pathlib import Path
import os
import zipfile
import io

from storage.folder_manager import list_scraped_files, get_total_stats
from app.logger import logger


def render():
    st.header("📁 Scraped Results")
    
    stats = get_total_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Normal Files", stats['normal_files'])
    with col2:
        st.metric("Novel Chapters", stats['novel_chapters'])
    with col3:
        st.metric("Total Files", stats['total_files'])
    with col4:
        st.metric("Storage Used", f"{stats['total_size_mb']} MB")
    
    st.divider()
    
    files = list_scraped_files()
    
    if not files['normal'] and not files['novels']:
        st.info("No files scraped yet. Go to Home to add URLs!")
        return
    
    tab1, tab2 = st.tabs(["📄 Normal Files", "📚 Novel Chapters"])
    
    with tab1:
        render_normal_files(files['normal'])
    
    with tab2:
        render_novel_files(files['novels'])


def render_normal_files(normal_files):
    if not normal_files:
        st.info("No normal files scraped yet")
        return
    
    for domain_data in normal_files:
        with st.expander(f"🌐 {domain_data['domain']} ({domain_data['file_count']} files)"):
            for filename in domain_data['files']:
                file_path = Path(domain_data['path']) / filename
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(filename)
                with col2:
                    if st.button(f"👁️ View", key=f"view_{filename}"):
                        show_file_content(file_path)


def render_novel_files(novel_files):
    if not novel_files:
        st.info("No novels scraped yet")
        return
    
    for novel_data in novel_files:
        with st.expander(f"📖 {novel_data['name']} ({novel_data['chapter_count']} chapters)"):
            folder_path = Path(novel_data['path'])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📦 Download ZIP", key=f"zip_{novel_data['name']}"):
                    download_novel_zip(folder_path, novel_data['name'])
            with col2:
                index_file = folder_path / "chapters_index.md"
                if index_file.exists():
                    if st.button(f"📋 View Index", key=f"index_{novel_data['name']}"):
                        show_file_content(index_file)
            
            chapters = sorted(folder_path.glob("chapter_*.md"))
            for chapter in chapters[:5]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(chapter.name)
                with col2:
                    if st.button(f"👁️", key=f"view_{chapter.name}"):
                        show_file_content(chapter)
            
            if len(chapters) > 5:
                st.caption(f"... and {len(chapters) - 5} more chapters")


def show_file_content(file_path: Path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        st.dialog(title=file_path.name)
        st.text_area("Content", content, height=400)
        
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")


def download_novel_zip(folder_path: Path, novel_name: str):
    try:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in folder_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(folder_path)
                    with open(file_path, 'rb') as f:
                        zf.writestr(str(arcname), f.read())
        
        zip_buffer.seek(0)
        
        st.download_button(
            label=f"Download {novel_name}.zip",
            data=zip_buffer,
            file_name=f"{novel_name}.zip",
            mime="application/zip"
        )
        
    except Exception as e:
        st.error(f"Error creating ZIP: {str(e)}")
