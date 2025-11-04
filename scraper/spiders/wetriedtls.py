from ..extractors.wetriedtls import WeTriedTlsExtractor
from .base import BaseNovelSpider


class WeTriedTlsSpider(BaseNovelSpider):
    name = "wetriedtls"
    source_site = "wetriedtls"
    language = "english"
    allowed_domains = ["wetriedtls.com"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extractor = WeTriedTlsExtractor()
        self.auto_crawl = kwargs.get("auto_crawl", False)

    def parse(self, response):
        # Use the base class's chapter parsing logic
        yield from self.parse_chapter(response)
