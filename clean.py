import argparse
import json
import os
import re
from pathlib import Path


def clean_text(text: str) -> str:
    """Clean up text by removing excessive whitespace and newlines."""
    # Clean up multiple spaces
    text = re.sub(r" +", " ", text)

    # Clean up spaces around newlines
    text = re.sub(r" *\n *", "\n", text)

    # Clean up multiple consecutive newlines (keep max 2 newlines = 1 blank line)
    text = re.sub(r"\n{2,}", "\n", text)

    # Replace ” with " and ‘ ’ with '
    text = text.replace("”", '"').replace("“", '"').replace("‘", "'").replace("’", "'")

    return text.strip()


def load_json(file_path: str) -> list:
    """Load JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_json(file_path: str, data: list):
    """Save JSON file."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clean_data(data: list) -> list:
    """Clean all aligned chapters in the data."""
    cleaned_data = []

    for item in data:
        cleaned_item = {}

        # Clean English content
        if "english" in item and "content" in item["english"]:
            cleaned_item["english"] = item["english"].copy()
            cleaned_item["english"]["content"] = clean_text(item["english"]["content"])
        else:
            cleaned_item["english"] = item.get("english", {})

        # Clean Korean content
        if "korean" in item and "content" in item["korean"]:
            cleaned_item["korean"] = item["korean"].copy()
            cleaned_item["korean"]["content"] = clean_text(item["korean"]["content"])
        else:
            cleaned_item["korean"] = item.get("korean", {})

        cleaned_data.append(cleaned_item)

    return cleaned_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clean up aligned Korean and English chapter content."
    )

    parser.add_argument(
        "--input_file",
        type=str,
        required=True,
        help="Path to the input JSON file containing aligned chapters",
    )

    parser.add_argument(
        "--output_file",
        type=str,
        default=None,
        help="Path to the output JSON file (default: input_file with '_cleaned' suffix)",
    )

    args = parser.parse_args()

    # Load data
    print(f"Loading data from: {args.input_file}")
    data = load_json(args.input_file)
    print(f"Loaded {len(data)} aligned chapters")

    # Clean data
    print("Cleaning content...")
    cleaned_data = clean_data(data)

    # Determine output file
    if args.output_file:
        output_file = args.output_file
    else:
        input_path = Path(args.input_file)
        output_file = (
            input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}"
        )

    # Save cleaned data
    print(f"Saving cleaned data to: {output_file}")
    save_json(output_file, cleaned_data)

    # Print statistics
    print("\n✅ Cleaning completed!")
    print(f"Input file: {args.input_file}")
    print(f"Output file: {output_file}")
    print(f"Total chapters processed: {len(cleaned_data)}")
