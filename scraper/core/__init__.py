"""
Scraper Core Module

Central orchestration layer for the scraper system.
Provides engine registry, fallback chains, and shared utilities.
"""

from scraper.core.captcha_detector import CaptchaDetector, captcha_detector
from scraper.core.engine_registry import (
    DEFAULT_FALLBACK_CHAINS,
    EngineRegistry,
    get_engine_registry,
)
from scraper.core.fallback_chain import (
    FallbackChain,
    FallbackResult,
    get_fallback_chain,
)
from scraper.core.metadata_extractor import MetadataExtractor, metadata_extractor
from scraper.core.page_extractor import PageExtractor
from scraper.core.session_manager import SessionManager, session_manager
from scraper.core.text_cleaner import TextCleaner, text_cleaner

__all__ = [
    # Page extraction
    "PageExtractor",
    # Engine registry
    "EngineRegistry",
    "get_engine_registry",
    "DEFAULT_FALLBACK_CHAINS",
    # Fallback chain
    "FallbackChain",
    "FallbackResult",
    "get_fallback_chain",
    # Session management
    "SessionManager",
    "session_manager",
    # Metadata extraction
    "MetadataExtractor",
    "metadata_extractor",
    # CAPTCHA detection
    "CaptchaDetector",
    "captcha_detector",
    # Text cleaning
    "TextCleaner",
    "text_cleaner",
]
