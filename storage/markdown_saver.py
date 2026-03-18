import json
from datetime import datetime
from pathlib import Path

from app.logger import logger


def save_normal_article(
    folder: Path,
    url: str,
    title: str,
    content: str,
    tags: list[str],
    word_count: int,
    output_format: str = "md",
    engine: str = "unknown",
    content_type: str = "article",
    custom_filename: str | None = None,
    genre: list[str] | None = None,
) -> Path:
    from utils.validators import generate_slug

    slug = custom_filename if custom_filename else generate_slug(url, title)

    # Use title as provided (already extracted in runner)
    display_title = title

    if output_format == "json":
        file_path = folder / f"{slug}.json"
        data = {
            "source_url": url,
            "title": display_title,
            "content": content,
            "tags": tags,
            "word_count": word_count,
            "engine": engine,
            "content_type": content_type,
            "scraped_at": datetime.now().strftime("%d-%m-%Y %H.%M.%S"),
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    elif output_format == "txt":
        file_path = folder / f"{slug}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"{display_title}\n\n")
            f.write(f"URL: {url}\n")
            f.write(f"Tags: {', '.join(tags)}\n")
            f.write(f"Word Count: {word_count}\n")
            f.write(f"Engine: {engine}\n")
            f.write(f"Scraped: {datetime.now().strftime('%d-%m-%Y %H.%M.%S')}\n")
            f.write("\n" + "=" * 50 + "\n\n")
            f.write(content)
    else:
        file_path = folder / f"{slug}.md"
        
        # Build frontmatter
        frontmatter = f"""---
source_url: "{url}"
title: "{display_title}"
engine: "{engine}"
content_type: "{content_type}"
"""
        # Add genre only for novels
        if genre:
            frontmatter += f"genre: {json.dumps(genre)}\n"
        
        frontmatter += f"""tags: {json.dumps(tags)}
word_count: {word_count}
scraped_at: "{datetime.now().strftime("%d-%m-%Y %H.%M.%S")}"
---

# {display_title}

{content}
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter)

    logger.info(f"Saved article to {file_path}")
    return file_path


def save_chapter(
    folder: Path,
    chapter_number: int,
    title: str,
    text: str,
    word_count: int,
    source_url: str,
    novel_name: str,
    genre: list[str],
    tags: list[str],
) -> Path:
    file_path = folder / f"chapter_{chapter_number}.md"

    safe_title = title if title and title != "None" else f"Chapter {chapter_number}"
    clean_tags = [t.rstrip(",") for t in tags if t]

    frontmatter = f"""---
chapter_number: {chapter_number}
title: "{safe_title}"
novel: "{novel_name}"
genre: {json.dumps(genre)}
tags: {json.dumps(clean_tags)}
word_count: {word_count}
source: "{source_url}"
scraped_at: {datetime.now().isoformat()}
---

# {safe_title}

{text}
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(frontmatter)

    logger.info(f"Saved chapter {chapter_number} to {file_path}")
    return file_path


def save_chapters_index(
    folder: Path,
    novel_name: str,
    genre: list[str],
    tags: list[str],
    chapters: list[dict],
    author: str = "Unknown",
) -> Path:
    file_path = folder / "chapters_index.md"

    clean_tags = [t.rstrip(",") for t in tags if t]
    total_words = sum(ch.get("word_count", 0) for ch in chapters)
    success_count = sum(1 for ch in chapters if ch.get("status") == "success")

    chapter_links = "\n".join(
        [
            f"- [Chapter {ch['number']}](chapter_{ch['number']}.md) - {ch.get('word_count', 0):,} words"
            for ch in chapters
            if ch.get("status") == "success"
        ]
    )

    failed_chapters = [ch for ch in chapters if ch.get("status") == "failed"]
    failed_list = ""
    if failed_chapters:
        failed_list = "\n\n### Failed Chapters\n" + "\n".join(
            [
                f"- Chapter {ch['number']}: {ch.get('error', 'Unknown error')}"
                for ch in failed_chapters
            ]
        )

    content = f"""# {novel_name}

**Author:** {author}

**Genre:** {", ".join(genre) if genre else "Not specified"}

**Tags:** {", ".join(clean_tags[:10]) if clean_tags else "Not specified"}

**Total Chapters:** {success_count}

**Total Words:** {total_words:,}

---

## Chapter List

{chapter_links}
{failed_list}

---

*Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Saved chapters index to {file_path}")
    return file_path
