from ..extractors.lightnovelpub import LightNovelPubExtractor
from .base import BaseNovelSpider


class LightNovelPubSpider(BaseNovelSpider):
    name = "lightnovelpup"
    source_site = "lightnovelpup"
    language = "english"
    allowed_domains = ["lightnovelpub.org"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extractor = LightNovelPubExtractor()
        self.auto_crawl = kwargs.get("auto_crawl", False)

    def parse(self, response):
        # Use the base class's chapter parsing logic
        yield from self.parse_chapter(response)
