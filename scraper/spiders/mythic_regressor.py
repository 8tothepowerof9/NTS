from ..extractors.mythic_regressor import MythicRegressorExtractor
from .base import BaseNovelSpider


class MythicRegressorSpider(BaseNovelSpider):
    name = "mythic_regressor"
    source_site = "mythic_regressor"
    language = "english"
    allowed_domains = ["mythicregressor.com"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extractor = MythicRegressorExtractor()
        self.auto_crawl = kwargs.get("auto_crawl", False)

    def parse(self, response):
        # Use the base class's chapter parsing logic
        yield from self.parse_chapter(response)
