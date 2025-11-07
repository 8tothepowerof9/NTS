import logging

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

    def extract_chapter_number(self, response) -> str:
        chapter_number = response.xpath(
            "/html/body/div/main/div[2]/nav[1]/div/div[1]/div[2]/h1/text()"
        ).get()

        # Clean up chapter number text
        chapter_number = chapter_number.strip() if chapter_number else ""

        return chapter_number if chapter_number else "-1"

    def extract_content(self, response) -> str:
        paragraphs = response.xpath('//*[@id="reader-container"]//p//text()').getall()

        # Join and clean up whitespace
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

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
