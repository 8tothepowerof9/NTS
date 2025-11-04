from ..extractors.booktoki import BookTokiExtractor
from .base import BaseNovelSpider


class BookTokiSpider(BaseNovelSpider):
    name = "booktoki"
    source_site = "booktoki"
    language = "korean"
    allowed_domains = ["booktoki469.com"]

    custom_settings = {
        "DOWNLOAD_DELAY": 8,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "AUTOTHROTTLE_START_DELAY": 3,
        "AUTOTHROTTLE_MAX_DELAY": 20,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extractor = BookTokiExtractor()
        self.auto_crawl = kwargs.get("auto_crawl", False)

    def parse(self, response):
        # Use the base class's chapter parsing logic
        yield from self.parse_chapter(response)
