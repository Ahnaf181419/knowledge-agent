"""
Extraction History Module
Tracks all successfully extracted URLs to prevent duplicates.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

HISTORY_FILE = Path(__file__).parent.parent / "history.json"

DEFAULT_HISTORY = {
    "normal": {},
    "novels": {}
}


class ExtractionHistory:
    def __init__(self):
        self.history = self._load_history()
    
    def _load_history(self) -> dict:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return {**DEFAULT_HISTORY, **json.load(f)}
            except:
                pass
        return DEFAULT_HISTORY.copy()
    
    def save(self):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
    
    def is_extracted(self, url: str) -> bool:
        return url in self.history.get("normal", {})
    
    def get_extracted_file(self, url: str) -> Optional[str]:
        entry = self.history.get("normal", {}).get(url)
        return entry.get("file") if entry else None
    
    def add_normal(self, url: str, file_path: str, word_count: int, scraper: str):
        self.history.setdefault("normal", {})[url] = {
            "file": str(file_path),
            "word_count": word_count,
            "scraper": scraper,
            "extracted_at": datetime.now().isoformat()
        }
        self.save()
    
    def is_novel_extracted(self, novel_url: str) -> bool:
        return novel_url in self.history.get("novels", {})
    
    def get_novel_chapters(self, novel_url: str) -> List[int]:
        entry = self.history.get("novels", {}).get(novel_url)
        return entry.get("chapters", []) if entry else []
    
    def set_novel_metadata(self, novel_url: str, folder: str, name: str,
                           genre: List[str], tags: List[str], author: str = "Unknown"):
        existing = self.history.get("novels", {}).get(novel_url, {})
        self.history.setdefault("novels", {})[novel_url] = {
            "folder": folder,
            "name": name,
            "author": author,
            "genre": genre,
            "tags": tags,
            "chapters": existing.get("chapters", []),
            "total_words": existing.get("total_words", 0),
            "first_extracted": existing.get("first_extracted", datetime.now().isoformat()),
            "last_extracted": None
        }
        self.save()
    
    def add_novel_chapter(self, novel_url: str, chapter: int, word_count: int):
        entry = self.history.get("novels", {}).get(novel_url)
        if entry:
            if chapter not in entry.get("chapters", []):
                entry.setdefault("chapters", []).append(chapter)
            entry["total_words"] = entry.get("total_words", 0) + word_count
            entry["last_extracted"] = datetime.now().isoformat()
            self.save()
    
    def get_novel_metadata(self, novel_url: str) -> Optional[dict]:
        return self.history.get("novels", {}).get(novel_url)
    
    def get_stats(self) -> dict:
        normal_count = len(self.history.get("normal", {}))
        novels = self.history.get("novels", {})
        novel_count = len(novels)
        total_chapters = sum(len(n.get("chapters", [])) for n in novels.values())
        total_words = sum(n.get("total_words", 0) for n in novels.values())
        normal_words = sum(n.get("word_count", 0) for n in self.history.get("normal", {}).values())
        
        return {
            "normal_links": normal_count,
            "novels": novel_count,
            "total_chapters": total_chapters,
            "total_words": total_words + normal_words
        }


history = ExtractionHistory()
