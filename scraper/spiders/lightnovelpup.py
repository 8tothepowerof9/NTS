from ..extractors.lightnovelpup import LightNovelPupExtractor
from .base import BaseNovelSpider


class LightNovelPupSpider(BaseNovelSpider):
    name = "lightnovelpup"
    source_site = "lightnovelpup"
    language = "english"
    allowed_domains = ["lightnovelpub.org"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extractor = LightNovelPupExtractor()
        self.auto_crawl = kwargs.get("auto_crawl", False)

    def parse(self, response):
        # Use the base class's chapter parsing logic
        yield from self.parse_chapter(response)
