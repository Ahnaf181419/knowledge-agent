import re
from pathlib import Path
from urllib.parse import urlparse

from utils.validators import generate_slug, get_domain, get_main_domain, is_novel_url


def get_base_output_folder() -> Path:
    from app.state import state

    folder_name: str = state.get_setting("output_folder", "output") or "output"
    return Path(__file__).parent.parent / folder_name


def get_output_folder() -> Path:
    folder = get_base_output_folder()
    folder.mkdir(exist_ok=True)
    return folder


def get_normal_folder(url: str) -> Path:
    """Get folder for normal (non-novel) URLs using main domain."""
    main_domain = get_main_domain(url)
    folder = get_base_output_folder() / main_domain
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_novel_folder(url: str) -> Path:
    """Get folder for novel chapters: Novels/domain/novel-slug/"""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    
    # Extract novel slug from path
    # e.g., /en/novel/3154/reborn-capital-tycoon/chapter-1 -> reborn-capital-tycoon
    novel_slug = None
    
    # Try to find novel slug in path - look for pattern /novel/{id}/{slug}
    path_parts = path.split("/")
    for i, part in enumerate(path_parts):
        if part.lower() == "novel":
            # Check next parts for the slug (skip numeric IDs)
            for j in range(i + 1, len(path_parts)):
                candidate = path_parts[j]
                # Skip numeric IDs
                if candidate and not candidate.isdigit() and "chapter" not in candidate.lower():
                    novel_slug = candidate
                    break
            break
    
    # Alternative: get last meaningful path segment before chapter
    if not novel_slug:
        for part in reversed(path_parts):
            if part and not part.isdigit() and "chapter" not in part.lower():
                novel_slug = part
                break
    
    if not novel_slug:
        # Fallback: use last path segment
        novel_slug = path_parts[-1] if path_parts else "unknown"
    
    # Clean the slug
    novel_slug = re.sub(r"[^\w\-]", "-", novel_slug.lower())
    novel_slug = re.sub(r"-+", "-", novel_slug).strip("-")
    
    main_domain = get_main_domain(url)
    folder = get_base_output_folder() / "Novels" / main_domain / novel_slug
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_novel_index_path(url: str) -> Path:
    """Get path for novel index.md file."""
    novel_folder = get_novel_folder(url)
    return novel_folder / "index.md"


def get_file_path(url: str, title: str | None = None, extension: str = "md") -> Path:
    folder = get_normal_folder(url)
    slug = generate_slug(url, title or "")

    filename = f"{slug}.{extension}"
    return folder / filename


def list_scraped_files() -> dict:
    files: dict[str, list] = {"normal": [], "novels": []}

    base = get_base_output_folder()
    if not base.exists():
        return files

    for domain_folder in base.iterdir():
        if domain_folder.is_dir():
            if domain_folder.name == "novels":
                for novel_folder in domain_folder.iterdir():
                    if novel_folder.is_dir():
                        chapters = list(novel_folder.glob("chapter_*.md"))
                        index_file = novel_folder / "chapters_index.md"

                        files["novels"].append(
                            {
                                "name": novel_folder.name,
                                "path": str(novel_folder),
                                "chapter_count": len(chapters),
                                "has_index": index_file.exists(),
                            }
                        )
            else:
                md_files = list(domain_folder.glob("*.md"))
                files["normal"].append(
                    {
                        "domain": domain_folder.name,
                        "path": str(domain_folder),
                        "file_count": len(md_files),
                        "files": [f.name for f in md_files],
                    }
                )

    return files


def get_total_stats() -> dict:
    files = list_scraped_files()

    total_normal = sum(f["file_count"] for f in files["normal"])
    total_novels = sum(n["chapter_count"] for n in files["novels"])

    base = get_base_output_folder()
    total_size = 0
    if base.exists():
        for folder in base.rglob("*"):
            if folder.is_file():
                total_size += folder.stat().st_size

    return {
        "normal_files": total_normal,
        "novel_chapters": total_novels,
        "total_files": total_normal + total_novels,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
    }
