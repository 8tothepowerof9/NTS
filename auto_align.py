import argparse
import json
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def load_chapters(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        logger.info(f"Loading chapters from {file_path}")
        return json.load(f)


def align_chapters(korean_chapters, english_chapters):
    aligned = []
    min_length = min(len(korean_chapters), len(english_chapters))

    logger.info(f"Aligning {min_length} chapters.")

    for i in range(min_length):
        aligned.append({"korean": korean_chapters[i], "english": english_chapters[i]})

    return aligned


def save_aligned_chapters(aligned_chapters, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(aligned_chapters, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automatically align Korean and English chapters from JSON files."
    )

    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Directory containing the Korean and English JSON files.",
    )
    parser.add_argument(
        "--korean_file",
        type=str,
        default="chapters_korean.json",
        help="Filename of the Korean chapters JSON file (default: chapters_korean.json)",
    )
    parser.add_argument(
        "--english_file",
        type=str,
        default="chapters_english.json",
        help="Filename of the English chapters JSON file (default: chapters_english.json)",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="aligned.json",
        help="Filename for the output aligned JSON file (default: aligned_chapters.json)",
    )

    args = parser.parse_args()

    korean_path = os.path.join(args.input_dir, args.korean_file)
    english_path = os.path.join(args.input_dir, args.english_file)
    output_path = os.path.join(args.input_dir, args.output_file)

    korean_chapters = load_chapters(korean_path)
    english_chapters = load_chapters(english_path)

    aligned_chapters = align_chapters(korean_chapters, english_chapters)

    save_aligned_chapters(aligned_chapters, output_path)

    print(f"✅ Aligned chapters saved to {output_path}")
