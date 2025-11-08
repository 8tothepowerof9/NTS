import logging

from bs4 import BeautifulSoup

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class LightNovelPubExtractor(BaseExtractor):
    """
    LightNovelPup extractor implementation.

    LightNovelPub is a website that hosts translation of various web novels. [Website](https://lightnovelpub.org/)

    The translations maybe from other translation sites.
    """

    def extract_novel_title(self, response) -> str:
        # Try CSS selector first (more reliable)
        title = response.css("div.novel-info a::text").get()
        if not title:
            # Fallback to XPath
            title = response.xpath(
                "/html/body/main/div[1]/div[1]/div[1]/div[1]/div[1]/a/text()"
            ).get()

        return title if title else ""

    def extract_chapter_number(self, response) -> str:
        # Try CSS selector
        chapter_text = response.css(".chapter-selector-btn::text").get()

        if not chapter_text:
            # Fallback to XPath
            chapter_text = response.xpath(
                "/html/body/main/div[1]/div[1]/div[1]/div[1]/div[1]/h1/text()"
            ).get()

        # Clean
        chapter_text = chapter_text.strip() if chapter_text else None

        return chapter_text if chapter_text else "-1"

    def extract_content(self, response) -> str:

        content_html = response.xpath('//*[@id="chapterText"]').get()

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
        # CSS selector for next button (most reliable)
        next_url = response.css("a.next-btn::attr(href)").get()

        if not next_url:
            # XPath fallback
            next_url = response.xpath('//a[contains(@class, "next-btn")]/@href').get()

        if not next_url:
            logger.warning("Could not find next chapter URL")
            return ""

        return response.urljoin(next_url)

    def extract_prev_chapter_url(self, response) -> str:
        # CSS selector for previous link (if it's an <a> tag)
        prev_url = response.css("a.prev-btn::attr(href)").get()

        if not prev_url:
            # XPath fallback
            prev_url = response.xpath('//a[contains(@class, "prev-btn")]/@href').get()

        if not prev_url:
            logger.info("No previous chapter link found (likely first chapter)")
            return ""

        return response.urljoin(prev_url)
