import json
import logging
from pathlib import Path
from typing import List, Optional

import scrapy

from .items import NovelChapterItem

logger = logging.getLogger(__name__)


class StoragePipeline:
    """
    Pipeline to store Korean and English chapters separately.

    Saves Korean chapters to one JSON file and English chapters to another.
    No pairing logic - just simple storage.
    """

    # Class-level shared storage (shared across all spider instances)
    _shared_korean_chapters: List[NovelChapterItem] = []
    _shared_english_chapters: List[NovelChapterItem] = []
    _shared_output_dir: Optional[Path] = None
    _shared_output_name: Optional[str] = None
    _spider_count: int = 0
    _completed_spiders: int = 0

    def __init__(
        self,
        output_dir: str = "output",
        output_name: str = "chapters",
    ):
        """
        Initialize the StoragePipeline.

        Args:
            output_dir (str, optional): Output directory. Defaults to "output".
            output_name (str, optional): Base name for output files. Defaults to "chapters".
        """
        self.output_dir = Path(output_dir)
        self.output_name = output_name

        # Initialize shared class variables on first instance
        if StoragePipeline._shared_output_dir is None:
            StoragePipeline._shared_output_dir = self.output_dir
            StoragePipeline._shared_output_name = output_name
            StoragePipeline._shared_korean_chapters = []
            StoragePipeline._shared_english_chapters = []
            StoragePipeline._spider_count = 0
            StoragePipeline._completed_spiders = 0

        logger.info(
            f"StoragePipeline output directory set to: {self.output_dir.resolve()}"
        )

    @classmethod
    def from_crawler(cls, crawler):
        """
        Create pipeline instance from crawler settings.

        Args:
            crawler: Scrapy crawler instance

        Returns:
            StoragePipeline: Configured pipeline instance
        """
        output_dir = crawler.settings.get("OUTPUT_DIR", "output")
        output_name = crawler.settings.get("OUTPUT_NAME", "chapters")

        return cls(
            output_dir=output_dir,
            output_name=output_name,
        )

    def open_spider(self, spider: scrapy.Spider):
        """
        Initialize resources when the spider opens.

        Args:
            spider (scrapy.Spider): The spider instance.
        """
        StoragePipeline._spider_count += 1
        logger.info(f"StoragePipeline started (Spider {StoragePipeline._spider_count})")

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"StoragePipeline output directory set to: {self.output_dir.absolute()}"
        )

    def process_item(self, item: NovelChapterItem, spider: scrapy.Spider):
        """Process each scraped item and store it."""
        if item["language"] == "korean":
            StoragePipeline._shared_korean_chapters.append(item)
            logger.debug(f"Stored Korean chapter {item.get('chapter_number')}")
        elif item["language"] == "english":
            StoragePipeline._shared_english_chapters.append(item)
            logger.debug(f"Stored English chapter {item.get('chapter_number')}")

        return item

    def close_spider(self, spider: scrapy.Spider):
        """Called when a spider is closed. Save only after all spiders finish."""
        StoragePipeline._completed_spiders += 1
        logger.info(
            f"Spider closed ({StoragePipeline._completed_spiders}/{StoragePipeline._spider_count} completed)"
        )

        # Only save when ALL spiders have finished
        if StoragePipeline._completed_spiders == StoragePipeline._spider_count:
            logger.info("All spiders completed. Saving chapters...")
            self._save_chapters()

            # Reset for next run
            StoragePipeline._shared_korean_chapters = []
            StoragePipeline._shared_english_chapters = []
            StoragePipeline._spider_count = 0
            StoragePipeline._completed_spiders = 0

    def _save_chapters(self):
        """Save Korean and English chapters to separate files."""
        output_dir = StoragePipeline._shared_output_dir or Path(".")
        output_name = StoragePipeline._shared_output_name or "chapters"

        # Save Korean chapters
        if StoragePipeline._shared_korean_chapters:
            korean_path = output_dir / f"{output_name}_korean.json"
            korean_data = [dict(ch) for ch in StoragePipeline._shared_korean_chapters]

            with open(korean_path, "w", encoding="utf-8") as f:
                json.dump(korean_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(korean_data)} Korean chapters to {korean_path}")

        # Save English chapters
        if StoragePipeline._shared_english_chapters:
            english_path = output_dir / f"{output_name}_english.json"
            english_data = [dict(ch) for ch in StoragePipeline._shared_english_chapters]

            with open(english_path, "w", encoding="utf-8") as f:
                json.dump(english_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(english_data)} English chapters to {english_path}")

        logger.info("StoragePipeline finished.")
