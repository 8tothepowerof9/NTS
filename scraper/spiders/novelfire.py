from ..extractors.novelfire import NovelFireExtractor
from .base import BaseNovelSpider


class NovelFireSpider(BaseNovelSpider):
    name = "novelfire"
    source_site = "novelfire"
    language = "english"
    allowed_domains = ["novelfire.net"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extractor = NovelFireExtractor()
        self.auto_crawl = kwargs.get("auto_crawl", False)

    def parse(self, response):
        # Use the base class's chapter parsing logic
        yield from self.parse_chapter(response)
