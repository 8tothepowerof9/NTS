import scrapy


class NovelChapterItem(scrapy.Item):
    """Common data structure for all novel chapters"""

    url = scrapy.Field()
    source_site = scrapy.Field()
    novel_title = scrapy.Field()
    chapter_number = scrapy.Field()
    content = scrapy.Field()
    author = scrapy.Field()
    language = scrapy.Field()
    timestamp = scrapy.Field()
    next_chapter_url = scrapy.Field()
    prev_chapter_url = scrapy.Field()
