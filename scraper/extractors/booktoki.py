import logging

from bs4 import BeautifulSoup

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class BookTokiExtractor(BaseExtractor):
    """
    BookToki extractor implementation.
    """

    def extract_novel_title(self, response) -> str:
        title = response.xpath(
            '//*[@id="at-main"]/div[2]/section/article/div[1]/div/div[2]/div/@title'
        ).get()
        return title.split("-")[0].strip()

    def extract_chapter_number(self, response) -> str:
        chapter_number = response.xpath(
            '//*[@id="at-main"]/div[2]/section/article/div[1]/div/div[2]/div/span/text()'
        ).get()

        # Clean the chapter number
        chapter_number = chapter_number.strip() if chapter_number else None

        return chapter_number if chapter_number else "-1"

    def extract_content(self, response) -> str:
        content_html = response.xpath('//*[@id="novel_content"]/div[2]').get()

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
        # Check for next button using XPath
        next_link = response.xpath('//*[@id="goNextBtn"]')

        if not next_link:
            logger.info("No next chapter link found")
            return ""

        # Extract the element (first match)
        next_element = next_link[0]

        # Check if it's a dummy link with alert (last chapter)
        onclick = next_element.xpath("@onclick").get()
        if onclick and "alert" in onclick:
            logger.info("Reached last chapter (detected alert in onclick)")
            return ""

        # Check if href is just a hash anchor (dummy link)
        href = next_element.xpath("@href").get()
        if not href or href.startswith("#"):
            logger.info("Next button is a dummy link (href='#next')")
            return ""

        # Valid next chapter URL
        return response.urljoin(href)

    def extract_prev_chapter_url(self, response) -> str:
        prev_link = response.xpath('//*[@id="goPrevBtn"]')

        if not prev_link:
            logger.info("No previous chapter link found (likely first chapter)")
            return ""

        # Extract the element (first match)
        prev_element = prev_link[0]

        # Check if it's a dummy link with alert (first chapter)
        onclick = prev_element.xpath("@onclick").get()
        if onclick and "alert" in onclick:
            logger.info("First chapter (detected alert in onclick)")
            return ""

        # Check if href is just a hash anchor (dummy link)
        href = prev_element.xpath("@href").get()
        if not href or href.startswith("#"):
            logger.info("Previous button is a dummy link")
            return ""

        # Valid previous chapter URL
        return response.urljoin(href)
