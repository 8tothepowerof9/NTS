import argparse

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from scraper.spiders import BookTokiSpider, LightNovelPupSpider


def run_paired_scraping(
    korean_urls,
    english_urls,
    auto_crawl=False,
    output_file=None,
    max_chapters=0,
    use_playwright=False,
):
    """
    Run both Korean and English spiders to scrape parallel translations.
    """
    settings = get_project_settings()

    if output_file:
        settings.set("PAIRED_OUTPUT_FILE", output_file)

    process = CrawlerProcess(settings)

    # Schedule spiders
    process.crawl(
        BookTokiSpider,
        start_urls=korean_urls,
        auto_crawl=auto_crawl,
        max_chapters=max_chapters,
        use_playwright=use_playwright,
    )
    process.crawl(
        LightNovelPupSpider,
        start_urls=english_urls,
        auto_crawl=auto_crawl,
        max_chapters=max_chapters,
        use_playwright=use_playwright,
    )

    process.start()
    print("\nScraping completed! Check the output directory for results.")


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
        "--output_file",
        type=str,
        default=None,
        help="Output JSON file name for paired results",
    )
    parser.add_argument(
        "--max_chapters",
        type=int,
        default=0,
        help="Maximum number of chapters to scrape (0 = no limit)",
    )
    parser.add_argument(
        "--use_playwright",
        type=lambda x: x.lower() in ["true", "1", "yes"],
        default=False,
        help="Use Playwright for dynamic content scraping (True/False)",
    )

    args = parser.parse_args()

    run_paired_scraping(
        korean_urls=args.korean_url,
        english_urls=args.english_url,
        auto_crawl=args.auto_crawl,
        output_file=args.output_file,
        max_chapters=args.max_chapters,
        use_playwright=args.use_playwright,
    )
