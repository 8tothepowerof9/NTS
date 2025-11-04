import logging
import re

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

    def extract_chapter_number(self, response) -> float:
        chapter_number = response.xpath(
            '//*[@id="at-main"]/div[2]/section/article/div[1]/div/div[2]/div/span/text()'
        ).get()

        match = re.search(r"\((\d+)(?:/\d+)?\)", chapter_number)
        if match:
            number = match.group(1)
            return float(number)

        logger.warning(f"Could not extract chapter number from: {chapter_number}")
        return -1

    def extract_content(self, response) -> str:
        paragraphs = response.xpath(
            '//*[@id="novel_content"]/div[2]//p/text()'
        ).getall()

        return "\n".join(p.strip() for p in paragraphs if p.strip())

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
