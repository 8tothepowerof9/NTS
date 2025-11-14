import json
from pathlib import Path


def estimate_tokens(text):
    """
    Rough token estimation (1 token ≈ 4 characters for English,
    1 token ≈ 2-3 characters for Korean/mixed text)
    For more accuracy, use the actual Aya tokenizer
    """
    # Conservative estimate for Korean + English
    return len(text) // 3


def convert_to_sharegpt_format(input_file, output_file, max_tokens=3072):
    """
    Convert your chapter format to ShareGPT format for Axolotl
    """
    with open(input_file, "r", encoding="utf-8") as f:
        chapters = json.load(f)

    converted_data = []
    skipped_chapters = []

    for idx, chapter in enumerate(chapters):
        korean_content = chapter["korean"]["content"]
        english_content = chapter["english"]["content"]

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
                    "estimated_tokens": total_tokens,
                    "korean_length": len(korean_content),
                    "english_length": len(english_content),
                }
            )
            continue

        # Create ShareGPT format
        conversation = {
            "messages": [
                {
                    "from": "user",
                    "value": f"Translate the following Korean webnovel chapter to English. Maintain the narrative style, character consistency, and natural flow.\n\n{korean_content}",
                },
                {"from": "assistant", "value": english_content},
            ]
        }

        converted_data.append(conversation)

    # Save converted data
    with open(output_file, "w", encoding="utf-8") as f:
        for item in converted_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Save report on skipped chapters
    if skipped_chapters:
        report_file = output_file.replace(".jsonl", "_skipped_report.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "total_skipped": len(skipped_chapters),
                    "skipped_chapters": skipped_chapters,
                    "summary": f"Skipped {len(skipped_chapters)} out of {len(chapters)} chapters",
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(
            f"⚠️  Skipped {len(skipped_chapters)} chapters (too long for {max_tokens} tokens)"
        )
        print(f"   Report saved to: {report_file}")

    print(f"✅ Converted {len(converted_data)} chapters")
    print(f"   Output saved to: {output_file}")

    return converted_data, skipped_chapters


# Usage
if __name__ == "__main__":
    input_file = "output/test.json"  # Your original data
    output_file = "training_data.jsonl"  # Axolotl format

    convert_to_sharegpt_format(
        input_file=input_file,
        output_file=output_file,
        max_tokens=8192,  # Adjust based on your RTX 5080 capacity
    )
