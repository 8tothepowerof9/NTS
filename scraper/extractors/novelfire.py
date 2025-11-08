import logging

from bs4 import BeautifulSoup

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class NovelFireExtractor(BaseExtractor):
    """
    NovelFire extractor implementation.

    NovelFire is a website that hosts translations of various web novels. [Website](https://novelfire.net/home)
    """

    def extract_novel_title(self, response) -> str:
        title = response.xpath(
            '//*[@id="chapter-article"]/section/div/div[1]/h1/a/text()'
        ).get()
        return title if title else ""

    def extract_chapter_number(self, response) -> str:
        chapter_number = response.xpath(
            '//*[@id="chapter-article"]/section/div/div[1]/h1/span[2]/text()'
        ).get()

        chapter_number = chapter_number.strip() if chapter_number else None

        return chapter_number if chapter_number else "-1"

    def extract_content(self, response) -> str:

        content_html = response.xpath('//*[@id="content"]').get()

        if not content_html:
            logger.warning("Content container not found")
            return ""

        soup = BeautifulSoup(content_html, "html.parser")

        # Define block-level elements
        block_elements = {
            "p",
            "div",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "li",
            "ul",
            "ol",
            "blockquote",
            "pre",
            "table",
            "tr",
            "section",
            "article",
            "header",
            "footer",
            "center",
        }

        def extract_text(element, result):
            """Recursively extract text with proper line break handling"""
            for child in element.children:
                if isinstance(child, str):
                    # It's a text node - preserve whitespace but normalize
                    text = " ".join(child.split())  # Normalize whitespace
                    if text:
                        # Add space before if needed (unless we just added a newline)
                        if (
                            result
                            and result[-1] != "\n"
                            and not result[-1].endswith(" ")
                        ):
                            result.append(" ")
                        result.append(text)
                elif child.name == "br":
                    # Explicit line break
                    result.append("\n")
                elif child.name in block_elements:
                    # Block element - add line break before
                    if result and result[-1] != "\n":
                        result.append("\n")
                    extract_text(child, result)
                    # Add line break after
                    if result and result[-1] != "\n":
                        result.append("\n")
                else:
                    # Inline element (i, strong, span, em, etc) - no line breaks
                    extract_text(child, result)

        result = []
        extract_text(soup, result)

        # Join and clean up
        text = "".join(result)

        return text.strip()

    def extract_next_chapter_url(self, response) -> str:
        next_url = response.xpath(
            '//*[@id="chapter-article"]/section/div/div[2]/a[2]/@href'
        ).get()

        if not next_url:
            logger.warning("Could not find next chapter URL")
            return ""

        return response.urljoin(next_url)

    def extract_prev_chapter_url(self, response) -> str:
        prev_url = response.xpath(
            '//*[@id="chapter-article"]/section/div/div[2]/a[1]/@href'
        ).get()

        if not prev_url:
            logger.warning("Could not find previous chapter URL")
            return ""

        return response.urljoin(prev_url)
