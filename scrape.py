import argparse
import re
import time
from urllib.parse import urlparse

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from scraper.spiders import (
    BookTokiSpider,
    LightNovelPubSpider,
    MythicRegressorSpider,
    NovelFireSpider,
    WeTriedTlsSpider,
)

SPIDER_MAP = {
    "booktoki": BookTokiSpider,
    "lightnovelpub": LightNovelPubSpider,
    "novelfire": NovelFireSpider,
    "wetriedtls": WeTriedTlsSpider,
    "mythicregressor": MythicRegressorSpider,
}


def detect_spider(url):
    """Detect spider based on URL, handling numbered subdomains"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")

    # Remove numbers from domain (e.g., booktoki469.com -> booktoki.com)
    domain_clean = re.sub(r"\d+", "", domain)

    # Try to find matching spider
    for key, spider in SPIDER_MAP.items():
        if key in domain or key in domain_clean:
            return spider, key

    return None, None


def run_paired_scraping(
    korean_urls,
    english_urls,
    auto_crawl=False,
    output_dir=None,
    output_name=None,
    kor_max_chapters=0,
    eng_max_chapters=0,
    use_playwright=False,
):
    """
    Run both Korean and English spiders to scrape chapters separately.
    """
    settings = get_project_settings()

    if output_dir:
        settings.set("OUTPUT_DIR", output_dir)

    if output_name:
        settings.set("OUTPUT_NAME", output_name)

    process = CrawlerProcess(settings)

    # Detect and schedule Korean spider
    korean_url = korean_urls[0]
    korean_spider, korean_name = detect_spider(korean_url)

    if korean_spider is None:
        raise ValueError(
            f"Unsupported Korean source site in URL: {korean_url}\n"
            f"Supported sites: {', '.join(SPIDER_MAP.keys())}"
        )

    print(f"✓ Detected Korean spider: {korean_name}")

    process.crawl(
        korean_spider,
        start_urls=korean_urls,
        auto_crawl=auto_crawl,
        max_chapters=kor_max_chapters,
        use_playwright=use_playwright,
    )

    # Detect and schedule English spider
    english_url = english_urls[0]
    english_spider, english_name = detect_spider(english_url)

    if english_spider is None:
        raise ValueError(
            f"Unsupported English source site in URL: {english_url}\n"
            f"Supported sites: {', '.join(SPIDER_MAP.keys())}"
        )

    print(f"✓ Detected English spider: {english_name}")

    process.crawl(
        english_spider,
        start_urls=english_urls,
        auto_crawl=auto_crawl,
        max_chapters=eng_max_chapters,
        use_playwright=use_playwright,
    )

    process.start()
    print("\n✅ Scraping completed! Check the output directory for results.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run parallel scraping of Korean and English novel sources."
    )

    parser.add_argument(
        "--korean_url",
        nargs="+",
        required=True,
        help="Starting URL(s) for Korean chapters (space-separated if multiple)",
    )
    parser.add_argument(
        "--english_url",
        nargs="+",
        required=True,
        help="Starting URL(s) for English chapters (space-separated if multiple)",
    )
    parser.add_argument(
        "--auto_crawl",
        type=lambda x: x.lower() in ["true", "1", "yes"],
        default=False,
        help="Whether to automatically follow next chapter links (True/False)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="output",
        help="Output directory for JSON files (default: output)",
    )
    parser.add_argument(
        "--output_name",
        type=str,
        default="chapters",
        help="Base name for output files (default: chapters)",
    )
    parser.add_argument(
        "--kor_max_chapters",
        type=int,
        default=0,
        help="Maximum number of Korean chapters to scrape (0 = no limit)",
    )
    parser.add_argument(
        "--eng_max_chapters",
        type=int,
        default=0,
        help="Maximum number of English chapters to scrape (0 = no limit)",
    )
    parser.add_argument(
        "--use_playwright",
        type=lambda x: x.lower() in ["true", "1", "yes"],
        default=False,
        help="Use Playwright for dynamic content scraping (True/False)",
    )

    args = parser.parse_args()

    start = time.time()

    run_paired_scraping(
        korean_urls=args.korean_url,
        english_urls=args.english_url,
        auto_crawl=args.auto_crawl,
        output_dir=args.output_dir,
        output_name=args.output_name,
        kor_max_chapters=args.kor_max_chapters,
        eng_max_chapters=args.eng_max_chapters,
        use_playwright=args.use_playwright,
    )

    end = time.time()
    elapsed = end - start
    print(f"\nTotal elapsed time: {elapsed:.2f} seconds")
