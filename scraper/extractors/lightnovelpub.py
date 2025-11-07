import logging

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
        # Get all text from p tags, including text within nested tags
        paragraphs = response.xpath('//*[@id="chapterText"]//p//text()').getall()

        # Join and clean up whitespace
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return "\n".join(paragraphs)

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
