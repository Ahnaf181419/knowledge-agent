import re

from rank_bm25 import BM25Okapi


class BM25Ranker:
    def __init__(self) -> None:
        self._documents: list[str] = []
        self._doc_ids: list[str] = []
        self._bm25: BM25Okapi | None = None

    def add_document(self, doc_id: str, content: str) -> None:
        normalized = self._normalize(content)
        self._documents.append(normalized)
        self._doc_ids.append(doc_id)
        if len(self._documents) > 0:
            tokenized = [doc.split() for doc in self._documents]
            self._bm25 = BM25Okapi(tokenized)

    def get_scores(self, query: str) -> list[float]:
        if self._bm25 is None or not self._documents:
            return []
        normalized_query = self._normalize(query)
        tokenized_query = normalized_query.split()
        return self._bm25.get_scores(tokenized_query).tolist()  # type: ignore[no-any-return]

    def is_duplicate(self, content: str, threshold: float = 0.8) -> bool:
        if self._bm25 is None or not self._documents:
            return False
        scores = self.get_scores(content)
        if not scores:
            return False
        max_score = max(scores)
        return max_score >= threshold

    def get_most_similar(self, content: str, limit: int = 5) -> list[tuple[str, float]]:
        if self._bm25 is None or not self._documents:
            return []
        scores = self.get_scores(content)
        paired = list(zip(self._doc_ids, scores, strict=True))
        paired.sort(key=lambda x: x[1], reverse=True)
        return paired[:limit]

    def clear(self) -> None:
        self._documents = []
        self._doc_ids = []
        self._bm25 = None

    def _normalize(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @property
    def document_count(self) -> int:
        return len(self._documents)
