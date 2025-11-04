from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    """Base class for site-specific content extractors"""

    @abstractmethod
    def extract_novel_title(self, response) -> str:
        """Extract novel title from response"""
        pass

    @abstractmethod
    def extract_chapter_number(self, response) -> float:
        """Extract chapter number"""
        pass

    @abstractmethod
    def extract_content(self, response) -> str:
        """Extract main chapter content"""
        pass

    @abstractmethod
    def extract_next_chapter_url(self, response) -> str:
        """Extract URL of next chapter"""
        pass

    @abstractmethod
    def extract_prev_chapter_url(self, response) -> str:
        """Extract URL of previous chapter"""
        pass
