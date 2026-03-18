"""
Content hashing utilities for duplicate detection.
"""

import hashlib


def compute_sha256(content: str) -> str:
    """
    Compute SHA256 hash of content.

    Args:
        content: Text content to hash

    Returns:
        Hexadecimal SHA256 hash
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_content_hash(content: str, normalize: bool = True) -> str:
    """
    Compute a normalized hash for duplicate detection.

    Args:
        content: Text content
        normalize: Whether to normalize whitespace

    Returns:
        Content hash
    """
    if normalize:
        normalized = " ".join(content.split())
    else:
        normalized = content
    return compute_sha256(normalized)


def compute_file_hash(file_path: str) -> str | None:
    """
    Compute SHA256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        Hexadecimal SHA256 hash or None if error
    """
    try:
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None
