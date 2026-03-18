from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEngine(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        pass

    @abstractmethod
    def scrape(self, url: str) -> str | None:
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name} (priority={self.priority})>"
