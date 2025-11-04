import logging
import re

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class WeTriedTlsExtractor(BaseExtractor):
    """
    WeTriedTls extractor implementation.

    WeTriedTls is a novel website that provides translations to novels that were discontinued by other fan translation groups.

    It is not a widely known and doesn't have many translated works, but offers human translations for some popular but abandoned novels.
    [Website](https://wetriedtls.com/)
    """

    def extract_novel_title(self, response) -> str:
        return response.xpath(
            "/html/body/div/main/div[2]/nav[1]/div/div[1]/div[2]/h2/text()"
        ).get()

    def extract_chapter_number(self, response) -> float:
        chapter_number = response.xpath(
            "/html/body/div/main/div[2]/nav[1]/div/div[1]/div[2]/h1/text()"
        ).get()

        # Extract the number
        match = re.search(r"Chapter (\d+)", chapter_number)
        if match:
            number = match.group(1)
            return float(number)
        logger.warning(f"Could not extract chapter number from: {chapter_number}")
        return -1

    def extract_content(self, response) -> str:
        paragraphs = response.xpath('//*[@id="reader-container"]//p/text()').getall()

        return "\n".join(paragraphs)

    def extract_next_chapter_url(self, response) -> str:
        next_url = response.xpath(
            "/html/body/div/main/div[2]/nav[2]/div/a[2]/@href"
        ).get()

        if not next_url:
            logger.warning("Could not find next chapter URL")
            return ""

        # If the URL is relative, convert to absolute
        return response.urljoin(next_url)

    def extract_prev_chapter_url(self, response) -> str:
        prev_url = response.xpath(
            "/html/body/div/main/div[2]/nav[2]/div/a[1]/@href"
        ).get()

        if not prev_url:
            logger.warning("Could not find previous chapter URL")
            return ""

        # If the URL is relative, convert to absolute
        return response.urljoin(prev_url)
