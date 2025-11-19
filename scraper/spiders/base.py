import logging
from datetime import datetime
from typing import Optional

import scrapy
from fake_useragent import UserAgent
from scrapy_playwright.page import PageMethod

from ..extractors.base import BaseExtractor
from ..items import NovelChapterItem

logger = logging.getLogger(__name__)


class BaseNovelSpider(scrapy.Spider):
    """Base spider class for all novel sites"""

    extractor: Optional[BaseExtractor] = None
    source_site = None
    language = None
    auto_crawl = False
    use_playwright = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ua = UserAgent()
        self.visited_urls = set()  # To track visited URLs

        self.max_chapters = int(kwargs.get("max_chapters", 0))  # 0 means unlimited
        self.chapters_scraped = 0

        start_urls = kwargs.get("start_urls")
        if start_urls:
            if isinstance(start_urls, str):
                self.start_urls = [start_urls]
            else:
                self.start_urls = start_urls
        elif not hasattr(self, "start_urls"):
            self.start_urls = []

    async def start(self):
        """Start requests with Playwright integration and human-like behavior."""
        for url in self.start_urls:

            yield scrapy.Request(
                url,
                callback=self.parse_chapter,
                headers={"User-Agent": self.ua.random},
                meta={
                    "playwright": self.use_playwright,
                    "playwright_include_page": True,
                    "playwright_page_goto_kwargs": {
                        "wait_until": "domcontentloaded",
                        "timeout": 60000,
                    },
                    "playwright_page_methods": [
                        PageMethod(
                            "evaluate",
                            """
                            page => require('playwright-stealth').stealth(page)
                            
                            () => {
                                window.scrollTo(0, Math.random() * 300);
                                const event = new MouseEvent('mousemove', {
                                    clientX: Math.random() * window.innerWidth,
                                    clientY: Math.random() * window.innerHeight
                                });
                                document.dispatchEvent(event);
                            }
                            """,
                        ),
                        PageMethod("wait_for_timeout", 500 + (hash(url) % 1000)),
                    ],
                },
            )

    def parse_chapter(self, response):
        """Common parsing logic for all novel chapters"""
        if self.extractor is None:
            raise NotImplementedError("extractor must be defined")

        # Mark URL as visited
        self.visited_urls.add(response.url)

        item = NovelChapterItem()
        item["url"] = response.url
        item["source_site"] = self.source_site
        item["language"] = self.language
        item["timestamp"] = datetime.now().isoformat()

        item["novel_title"] = self.extractor.extract_novel_title(response)
        item["chapter_number"] = self.extractor.extract_chapter_number(response)
        item["content"] = self.extractor.extract_content(response)
        item["next_chapter_url"] = self.extractor.extract_next_chapter_url(response)
        item["prev_chapter_url"] = self.extractor.extract_prev_chapter_url(response)

        logger.info(
            f"Scraped chapter {item.get('chapter_number')} from {item.get('url')}"
        )

        # Increment chapter counter
        self.chapters_scraped += 1

        yield item

        # Check if max_chapters limit is reached
        if self.max_chapters > 0 and self.chapters_scraped >= self.max_chapters:
            logger.info(
                f"Reached max_chapters limit ({self.max_chapters}). Stopping auto-crawl."
            )
            return

        # Auto-crawl next chapter with validation
        if self.auto_crawl and item["next_chapter_url"]:
            next_url = item["next_chapter_url"]

            # Check if already visited
            if next_url in self.visited_urls:
                logger.info(f"Already visited next chapter URL: {next_url}")
                return

            # Validate the URL before following
            if self._is_valid_next_url(next_url, response.url):
                logger.info(
                    f"Following next chapter: {next_url} ({self.chapters_scraped}/{self.max_chapters or 'unlimited'})"
                )
                yield scrapy.Request(
                    next_url,
                    callback=self.parse_chapter,
                    headers={"User-Agent": self.ua.random},
                    dont_filter=True,
                    meta={
                        "playwright": self.use_playwright,
                        "playwright_include_page": True,
                        "playwright_page_goto_kwargs": {
                            "wait_until": "domcontentloaded",
                            "timeout": 60000,
                        },
                    },
                )
            else:
                logger.info(f"Skipping invalid next URL: {next_url}")

    def _is_valid_next_url(self, next_url: str, current_url: str) -> bool:
        """
        Validate if the next URL is a real chapter link.

        Args:
            next_url: The extracted next chapter URL
            current_url: The current page URL

        Returns:
            bool: True if valid, False if it's a dummy link
        """
        if not next_url:
            return False

        # Check for hash anchors (dummy links)
        if next_url.startswith("#") or "/#" in next_url:
            logger.debug(f"Rejected hash anchor: {next_url}")
            return False

        # Check if it's the same URL (some sites do this)
        if next_url == current_url:
            logger.debug(f"Rejected same URL: {next_url}")
            return False

        # Check for javascript: pseudo-protocol
        if next_url.lower().startswith("javascript:"):
            logger.debug(f"Rejected javascript link: {next_url}")
            return False

        return True
