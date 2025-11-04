import json
import logging
from pathlib import Path
from typing import Dict, List, Literal, Optional

import scrapy

from .items import NovelChapterItem

logger = logging.getLogger(__name__)


class PairingPipeline:
    """
    Pipeline to pair Korean source chapters with English translations.

    Stores chapters in memory and pairs them by chapter number or by the order they were scraped.

    Outputs paired chapters to a JSON file under the specified directory.
    """

    # Class-level shared storage (shared across all spider instances)
    _shared_korean_chapters: List[NovelChapterItem] = []
    _shared_english_chapters: List[NovelChapterItem] = []
    _shared_output_file: Optional[str] = None
    _shared_output_dir: Optional[Path] = None
    _shared_pair_by: Optional[str] = None
    _spider_count: int = 0
    _completed_spiders: int = 0

    def __init__(
        self,
        output_file: str,
        output_dir: str = "output",
        pair_by: Literal["chapter_number", "order"] = "order",
    ):
        """
        Initialize the PairingPipeline.

        Args:
            output_file (str): Output filename for paired chapters.
            output_dir (str, optional): Json output directory. Defaults to "output".
            pair_by (Literal["chapter_number", "order"], optional): Determine how to pair the chapters. Defaults to "order".
        """
        self.output_file = output_file
        self.output_dir = Path(output_dir)
        self.pair_by = pair_by

        # Initialize shared class variables on first instance
        if PairingPipeline._shared_output_file is None:
            PairingPipeline._shared_output_file = output_file
            PairingPipeline._shared_output_dir = self.output_dir
            PairingPipeline._shared_pair_by = pair_by
            PairingPipeline._shared_korean_chapters = []
            PairingPipeline._shared_english_chapters = []
            PairingPipeline._spider_count = 0
            PairingPipeline._completed_spiders = 0

        logger.info(
            f"PairingPipeline output directory set to: {self.output_dir.resolve()}"
        )

    @classmethod
    def from_crawler(cls, crawler):
        """
        Create pipeline instance from crawler settings.

        Args:
            crawler: Scrapy crawler instance

        Returns:
            PairingPipeline: Configured pipeline instance
        """
        output_file = crawler.settings.get("PAIRED_OUTPUT_FILE", "paired_chapters.json")
        output_dir = crawler.settings.get("OUTPUT_DIR", "output")
        pair_by = crawler.settings.get("PAIR_BY", "order")

        return cls(
            output_file=output_file,
            output_dir=output_dir,
            pair_by=pair_by,
        )

    def open_spider(self, spider: scrapy.Spider):
        """
        Initialize resources when the spider opens.

        Args:
            spider (scrapy.Spider): The spider instance.
        """
        PairingPipeline._spider_count += 1
        logger.info(
            f"PairingPipeline started with pair_by='{self.pair_by}' (Spider {PairingPipeline._spider_count})"
        )

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"PairingPipeline output directory set to: {self.output_dir.absolute()}"
        )

    def process_item(self, item: NovelChapterItem, spider: scrapy.Spider):
        """Process each scraped item and store it for pairing."""
        if item["language"] == "korean":
            PairingPipeline._shared_korean_chapters.append(item)
            logger.debug(f"Stored Korean chapter {item.get('chapter_number')}")
        elif item["language"] == "english":
            PairingPipeline._shared_english_chapters.append(item)
            logger.debug(f"Stored English chapter {item.get('chapter_number')}")

        return item

    def close_spider(self, spider: scrapy.Spider):
        """Called when a spider is closed. Pair and save only after all spiders finish."""
        PairingPipeline._completed_spiders += 1
        logger.info(
            f"Spider closed ({PairingPipeline._completed_spiders}/{PairingPipeline._spider_count} completed)"
        )

        # Only pair and save when ALL spiders have finished
        if PairingPipeline._completed_spiders == PairingPipeline._spider_count:
            logger.info("All spiders completed. Starting pairing process...")
            self._pair_and_save()

            # Reset for next run
            PairingPipeline._shared_korean_chapters = []
            PairingPipeline._shared_english_chapters = []
            PairingPipeline._spider_count = 0
            PairingPipeline._completed_spiders = 0

    def _pair_and_save(self):
        """Pair Korean and English chapters and save to file."""
        paired_chapters = []

        if PairingPipeline._shared_pair_by == "chapter_number":
            paired_chapters = self._pair_by_chapter_number()
        else:  # pair_by == "order"
            paired_chapters = self._pair_by_order()

        # Save to JSON
        output_dir = PairingPipeline._shared_output_dir or Path(".")
        output_file = PairingPipeline._shared_output_file or "paired_chapters.json"
        output_path = output_dir / output_file

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(paired_chapters, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(paired_chapters)} paired chapters to {output_path}")

        # Log unpaired chapters
        korean_chapters_used = {p["korean"]["chapter_number"] for p in paired_chapters}
        english_chapters_used = {
            p["english"]["chapter_number"] for p in paired_chapters
        }

        unpaired_korean = [
            ch["chapter_number"]
            for ch in PairingPipeline._shared_korean_chapters
            if ch["chapter_number"] not in korean_chapters_used
        ]
        unpaired_english = [
            ch["chapter_number"]
            for ch in PairingPipeline._shared_english_chapters
            if ch["chapter_number"] not in english_chapters_used
        ]

        if unpaired_korean:
            logger.warning(
                f"Unpaired Korean chapters ({len(unpaired_korean)}): {unpaired_korean}"
            )
        if unpaired_english:
            logger.warning(
                f"Unpaired English chapters ({len(unpaired_english)}): {unpaired_english}"
            )

        logger.info("PairingPipeline finished.")

    def _pair_by_chapter_number(self) -> List[Dict]:
        """Pair chapters by matching chapter numbers."""
        korean_dict = {
            ch["chapter_number"]: ch for ch in PairingPipeline._shared_korean_chapters
        }
        english_dict = {
            ch["chapter_number"]: ch for ch in PairingPipeline._shared_english_chapters
        }

        paired = []
        for chapter_num in sorted(set(korean_dict.keys()) & set(english_dict.keys())):
            paired.append(
                {
                    "korean": dict(korean_dict[chapter_num]),
                    "english": dict(english_dict[chapter_num]),
                }
            )

        return paired

    def _pair_by_order(self) -> List[Dict]:
        """Pair chapters by the order they were scraped."""
        min_length = min(
            len(PairingPipeline._shared_korean_chapters),
            len(PairingPipeline._shared_english_chapters),
        )

        paired = []
        for i in range(min_length):
            paired.append(
                {
                    "korean": dict(PairingPipeline._shared_korean_chapters[i]),
                    "english": dict(PairingPipeline._shared_english_chapters[i]),
                }
            )

        return paired
