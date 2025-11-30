import json
import random
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

    # Replace " with " and ' ' with '
    text = text.replace("”", '"').replace("“", '"').replace("‘", "'").replace("’", "'")
    text = text.replace("❝", '"').replace("❞", '"')
    text = text.replace("❛", "'").replace("❜", "'")

    # Replace alternatives with [ and ]
    text = (
        text.replace("『", "[").replace("』", "]").replace("「", "[").replace("」", "]")
    )
    text = text.replace("｢", "[").replace("｣", "]")
    text = text.replace("【", "[").replace("】", "]")
    text = text.replace("⦗", "[").replace("⦘", "]")
    text = text.replace("〖", "[").replace("〗", "]")
    text = text.replace("⟦", "[").replace("⟧", "]")
    text = text.replace("⟨", "[").replace("⟩", "]")
    text = text.replace("《", "[").replace("》", "]")
    # Replace more alternatives
    text = text.replace("﹁", "[").replace("﹂", "]")
    text = text.replace("﹃", "[").replace("﹄", "]")
    text = text.replace("❬", "[").replace("❭", "]")
    text = text.replace("❮", "[").replace("❯", "]")
    text = text.replace("❰", "[").replace("❱", "]")

    # Add \n between consecutive ] and [
    text = re.sub(r"\]\s*\[", "]\n[", text)

    return text.strip()


def estimate_tokens(text):
    """
    Rough token estimation (1 token ≈ 4 characters for English,
    1 token ≈ 2-3 characters for Korean/mixed text)
    For more accuracy, use the actual Aya tokenizer
    """
    # Conservative estimate for Korean + English
    return len(text) // 3


def clean_chapter(chapter):
    """Clean a single aligned chapter."""
    cleaned_chapter = {}

    # Clean English content
    if "english" in chapter and "content" in chapter["english"]:
        cleaned_chapter["english"] = chapter["english"].copy()
        cleaned_chapter["english"]["content"] = clean_text(
            chapter["english"]["content"]
        )
    else:
        cleaned_chapter["english"] = chapter.get("english", {})

    # Clean Korean content
    if "korean" in chapter and "content" in chapter["korean"]:
        cleaned_chapter["korean"] = chapter["korean"].copy()
        cleaned_chapter["korean"]["content"] = clean_text(chapter["korean"]["content"])
    else:
        cleaned_chapter["korean"] = chapter.get("korean", {})

    return cleaned_chapter


def process_aligned_file(aligned_file_path, max_tokens=10240, model_type="cohere"):
    """Process a single aligned.json file: clean and convert to ShareGPT format."""
    print(f"\nProcessing: {aligned_file_path}")

    # Load aligned data
    with open(aligned_file_path, "r", encoding="utf-8") as f:
        chapters = json.load(f)

    print(f"   Found {len(chapters)} chapters")

    # Clean and convert chapters
    converted_data = []
    skipped_chapters = []

    for idx, chapter in enumerate(chapters):
        # Clean the chapter first
        cleaned_chapter = clean_chapter(chapter)

        korean_content = cleaned_chapter["korean"].get("content", "")
        english_content = cleaned_chapter["english"].get("content", "")

        # Skip if either content is empty
        if not korean_content or not english_content:
            skipped_chapters.append(
                {
                    "index": idx,
                    "reason": "empty_content",
                    "korean_length": len(korean_content),
                    "english_length": len(english_content),
                }
            )
            continue

        # Estimate total tokens (including instruction overhead)
        kr_tokens = estimate_tokens(korean_content)
        en_tokens = estimate_tokens(english_content)
        instruction_overhead = 50  # Approximate tokens for instruction text
        total_tokens = kr_tokens + en_tokens + instruction_overhead

        # Skip chapters that are too long
        if total_tokens > max_tokens:
            skipped_chapters.append(
                {
                    "index": idx,
                    "reason": "too_long",
                    "estimated_tokens": total_tokens,
                    "korean_length": len(korean_content),
                    "english_length": len(english_content),
                }
            )
            continue

        # Create ShareGPT format based on model_type
        if model_type == "cohere":
            # Cohere format with system message
            conversation = {
                "messages": [
                    {
                        "from": "system",
                        "value": "You are a professional webnovel translator. Translate the following Korean text into flowing, immersive English. Use terminology appropriate for the setting.",
                    },
                    {
                        "from": "user",
                        "value": korean_content,
                    },
                    {"from": "assistant", "value": english_content},
                ]
            }
        else:
            # Gemma format without system message (instruction in user message)
            conversation = {
                "messages": [
                    {
                        "from": "user",
                        "value": f"You are a professional webnovel translator. Translate the following Korean text into flowing, immersive English. Use terminology appropriate for the setting.\n\n{korean_content}",
                    },
                    {"from": "assistant", "value": english_content},
                ]
            }

        converted_data.append(conversation)

    print(f"    Converted: {len(converted_data)} chapters")
    if skipped_chapters:
        print(f"     Skipped: {len(skipped_chapters)} chapters")

    return converted_data, skipped_chapters


def main():
    """Main function to process all aligned.json files in output folder."""
    output_dir = Path("output")
    model_type = "nemo"

    if not output_dir.exists():
        print(f"Error: '{output_dir}' directory not found")
        return

    # Find all aligned.json files
    aligned_files = list(output_dir.rglob("aligned.json"))

    if not aligned_files:
        print(f"No aligned.json files found in '{output_dir}'")
        return

    print(f"🔍 Found {len(aligned_files)} aligned.json files")

    # Process all files
    all_converted_data = []
    all_skipped_reports = {}
    max_tokens = 10240  # 10k tokens

    for aligned_file in aligned_files:
        novel_name = aligned_file.parent.name
        converted_data, skipped_chapters = process_aligned_file(
            aligned_file, max_tokens=max_tokens, model_type=model_type
        )

        all_converted_data.extend(converted_data)

        if skipped_chapters:
            all_skipped_reports[novel_name] = {
                "file": str(aligned_file),
                "total_skipped": len(skipped_chapters),
                "skipped_chapters": skipped_chapters,
            }

    # Shuffle the training data
    print(f"\nShuffling data...")
    random.shuffle(all_converted_data)

    # Split into train and test (90% / 10%)
    split_idx = int(len(all_converted_data) * 0.9)
    train_data = all_converted_data[:split_idx]
    test_data = all_converted_data[split_idx:]

    print(f"Split: {len(train_data)} train, {len(test_data)} test")

    # Save training data
    train_file = output_dir / "training_data.jsonl"
    print(f"\nSaving training data...")

    with open(train_file, "w", encoding="utf-8") as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"   Saved to: {train_file}")

    # Save test data
    test_file = output_dir / "test_data.jsonl"
    print(f"Saving test data...")

    with open(test_file, "w", encoding="utf-8") as f:
        for item in test_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"   Saved to: {test_file}")

    # Save skipped chapters report
    if all_skipped_reports:
        report_file = output_dir / "training_data_skipped_report.json"
        total_skipped = sum(
            report["total_skipped"] for report in all_skipped_reports.values()
        )

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "max_tokens": max_tokens,
                    "total_novels": len(aligned_files),
                    "total_chapters_converted": len(all_converted_data),
                    "train_chapters": len(train_data),
                    "test_chapters": len(test_data),
                    "total_chapters_skipped": total_skipped,
                    "novels": all_skipped_reports,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"\nSkipped Report:")
        print(f"   Total skipped: {total_skipped} chapters")
        print(f"   Report saved to: {report_file}")

    # Print summary
    print(f"\n" + "=" * 60)
    print(f"TRAINING DATA PREPARATION COMPLETE")
    print(f"=" * 60)
    print(f"Novels processed: {len(aligned_files)}")
    print(f"Total chapters converted: {len(all_converted_data)}")
    print(f"Train chapters: {len(train_data)} (90%)")
    print(f"Test chapters: {len(test_data)} (10%)")
    print(f"Max tokens limit: {max_tokens}")
    print(f"Training file: {train_file}")
    print(f"Test file: {test_file}")
    print(f"=" * 60)


if __name__ == "__main__":
    main()
