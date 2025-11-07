import logging

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
        # Get all text from p tags, including text within nested tags
        paragraphs = response.xpath('//*[@id="content"]/p//text()').getall()

        # Join and clean up whitespace
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return "\n".join(paragraphs)

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
