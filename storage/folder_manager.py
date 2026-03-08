from pathlib import Path
from urllib.parse import urlparse
import re

from utils.validators import get_domain, generate_slug


def get_base_output_folder() -> Path:
    from app.container import container
    folder_name: str = container.state_repo.get_setting('output_folder', 'output') or 'output'
    return Path(__file__).parent.parent / folder_name


def get_output_folder() -> Path:
    folder = get_base_output_folder()
    folder.mkdir(exist_ok=True)
    return folder


def get_normal_folder(url: str) -> Path:
    domain = get_domain(url)
    folder = get_base_output_folder() / domain
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_novel_folder(novel_url: str) -> Path:
    parsed = urlparse(novel_url)
    path = parsed.path.strip('/')
    
    if '/' in path:
        parts = path.split('/')
        novel_slug = parts[-1] if parts[-1] else parts[-2]
    else:
        novel_slug = path
    
    novel_slug = re.sub(r'[^\w\-]', '-', novel_slug.lower())
    novel_slug = re.sub(r'-+', '-', novel_slug)
    
    folder = get_base_output_folder() / "novels" / novel_slug
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_file_path(url: str, title: str | None = None, extension: str = 'md') -> Path:
    folder = get_normal_folder(url)
    slug = generate_slug(url, title or '')
    
    filename = f"{slug}.{extension}"
    return folder / filename


def list_scraped_files() -> dict:
    files = {
        'normal': [],
        'novels': []
    }
    
    base = get_base_output_folder()
    if not base.exists():
        return files
    
    for domain_folder in base.iterdir():
        if domain_folder.is_dir():
            if domain_folder.name == 'novels':
                for novel_folder in domain_folder.iterdir():
                    if novel_folder.is_dir():
                        chapters = list(novel_folder.glob('chapter_*.md'))
                        index_file = novel_folder / 'chapters_index.md'
                        
                        files['novels'].append({
                            'name': novel_folder.name,
                            'path': str(novel_folder),
                            'chapter_count': len(chapters),
                            'has_index': index_file.exists()
                        })
            else:
                md_files = list(domain_folder.glob('*.md'))
                files['normal'].append({
                    'domain': domain_folder.name,
                    'path': str(domain_folder),
                    'file_count': len(md_files),
                    'files': [f.name for f in md_files]
                })
    
    return files


def get_total_stats() -> dict:
    files = list_scraped_files()
    
    total_normal = sum(f['file_count'] for f in files['normal'])
    total_novels = sum(n['chapter_count'] for n in files['novels'])
    
    base = get_base_output_folder()
    total_size = 0
    if base.exists():
        for folder in base.rglob('*'):
            if folder.is_file():
                total_size += folder.stat().st_size
    
    return {
        'normal_files': total_normal,
        'novel_chapters': total_novels,
        'total_files': total_normal + total_novels,
        'total_size_mb': round(total_size / (1024 * 1024), 2)
    }
