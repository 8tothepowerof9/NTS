import logging
import re

from bs4 import BeautifulSoup

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class MythicRegressorExtractor(BaseExtractor):
    """
    Mythic Regressor extractor implementation.
    Mythic Regressor is a web novel translation site. [Website](https://mythicregressor.com/)

    Offer small selection of translation but high quality

    Args:
        BaseExtractor (_type_): _description_
    """

    def extract_novel_title(self, response) -> str:
        title = response.xpath(
            '//*[@id="manga-reading-nav-head"]/div/div[1]/div/div[1]/ol/li[2]/a/text()'
        ).get()

        # strip
        title = title.strip() if title else None

        return title if title else ""

    def extract_chapter_number(self, response) -> str:
        chapter_number = response.xpath(
            '//*[@id="chapter-heading"]/text()[normalize-space()]'
        ).get()

        if not chapter_number:
            chapter_number = response.css("#chapter-heading::text").get()

        chapter_number = chapter_number.strip() if chapter_number else None

        return chapter_number if chapter_number else "-1"

    def extract_content(self, response) -> str:
        content_html = response.xpath(
            "/html/body/div[1]/div/div[2]/div/div/div/div/div/div/div[1]/div[2]/div/div/div/div[2]"
        ).get()

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
                    # Inline element (i, strong, span, etc) - no line breaks
                    extract_text(child, result)

        result = []
        extract_text(soup, result)

        # Join and clean up
        text = "".join(result)

        return text.strip()

    def extract_next_chapter_url(self, response) -> str:
        next_url = (
            response.xpath(
                '//*[@id="manga-reading-nav-head"]//a[@href][contains(@class, "next")]/@href'
            ).get()
            or response.css("a.next_page::attr(href)").get()
        )

        if not next_url:
            logger.warning("Next chapter URL not found.")
            return ""

        return response.urljoin(next_url)

    def extract_prev_chapter_url(self, response) -> str:
        prev_url = (
            response.xpath(
                '//*[@id="manga-reading-nav-head"]//a[@href][contains(@class, "prev")]/@href'
            ).get()
            or response.css("a.prev_page::attr(href)").get()
        )

        if not prev_url:
            logger.warning("Previous chapter URL not found.")
            return ""

        return response.urljoin(prev_url)
