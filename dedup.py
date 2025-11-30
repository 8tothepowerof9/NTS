import json
import re

from datasketch import MinHash, MinHashLSH

# --- CONFIGURATION ---
INPUT_FILE = "output/training_data.jsonl"
OUTPUT_FILE = "training_data_cleaned.jsonl"
DUPLICATE_REPORT_FILE = "duplicate_report.json"
SIMILARITY_THRESHOLD = 0.70
NUM_PERMS = 128  # Accuracy setting (128 is standard)


def get_korean_input(record):
    """
    Extracts the Korean text from your JSONL structure.
    Adjust the keys below if your data format is different.
    """
    try:
        # Check if 'messages' key exists (Standard ShareGPT/Chat format)
        if "messages" in record:
            for message in record["messages"]:
                # Adjust these roles based on your data ("user", "human", "from", etc.)
                if message.get("role") == "assistant" or message.get("from") == "gpt":
                    return message.get("content") or message.get("value")

        # Fallback: if your JSONL is just {"korean": "...", "english": "..."}
        if "korean" in record:
            return record["korean"]

        return str(record)  # Fallback to stringifying the whole line
    except Exception:
        return str(record)


def preprocess(text):
    """
    Breaks text into unique words (tokens) to compare.
    """
    if not text:
        return []
    # Lowercase and split by spaces/punctuation
    text = text.lower()
    tokens = re.findall(r"\w+", text)
    return tokens


def main():
    print(f"--- Processing {INPUT_FILE} ---")

    raw_data = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                raw_data.append(json.loads(line))

    print(f"Total Initial Rows: {len(raw_data)}")

    # --- PART 1: EXACT DEDUPLICATION ---
    unique_data = []
    seen_hashes = set()
    exact_duplicates = 0
    exact_duplicate_indices = []

    for idx, entry in enumerate(raw_data):
        text_content = get_korean_input(entry)
        # Create a simple hash of the text
        text_hash = hash(text_content)

        if text_hash in seen_hashes:
            exact_duplicates += 1
            exact_duplicate_indices.append(idx)
        else:
            seen_hashes.add(text_hash)
            unique_data.append(entry)

    print(f"Exact Duplicates Removed: {exact_duplicates}")
    if exact_duplicate_indices:
        print(
            f"  Indices: {exact_duplicate_indices[:20]}{'...' if len(exact_duplicate_indices) > 20 else ''}"
        )

    # --- PART 2: FUZZY (NEAR) DEDUPLICATION ---
    print("Running Fuzzy Deduplication (MinHash)...")

    lsh = MinHashLSH(threshold=SIMILARITY_THRESHOLD, num_perm=NUM_PERMS)
    minhashes = {}

    # Generate MinHash signatures for all unique records
    for idx, entry in enumerate(unique_data):
        text = get_korean_input(entry)
        tokens = preprocess(text)

        m = MinHash(num_perm=NUM_PERMS)
        for token in tokens:
            m.update(token.encode("utf8"))

        minhashes[idx] = m
        # Store in LSH index
        lsh.insert(f"row_{idx}", m)

    # Query the index to find duplicates
    seen_fuzzy = set()
    final_data = []
    fuzzy_duplicates = 0
    fuzzy_duplicate_groups = []  # Store duplicate groups with indices

    for idx, entry in enumerate(unique_data):
        if idx in seen_fuzzy:
            continue  # Already marked as a duplicate

        m = minhashes[idx]
        # Ask LSH: "Who is similar to me?"
        result = lsh.query(m)

        # Collect similar indices
        similar_indices = []
        for key in result:
            other_idx = int(key.split("_")[1])
            if other_idx > idx:  # Only remove "future" duplicates to keep the first one
                if other_idx not in seen_fuzzy:
                    seen_fuzzy.add(other_idx)
                    fuzzy_duplicates += 1
                    similar_indices.append(other_idx)

        # Record the duplicate group if any were found
        if similar_indices:
            fuzzy_duplicate_groups.append(
                {
                    "kept_index": idx,
                    "removed_indices": similar_indices,
                    "text_preview": get_korean_input(entry)[:100],
                }
            )

        if idx not in seen_fuzzy:
            final_data.append(entry)

    print(f"Near (Fuzzy) Duplicates Removed: {fuzzy_duplicates}")
    print(f"Duplicate Groups Found: {len(fuzzy_duplicate_groups)}")

    # Show first few duplicate groups
    if fuzzy_duplicate_groups:
        print("\nFirst 5 Near-Duplicate Groups:")
        for i, group in enumerate(fuzzy_duplicate_groups[:5], 1):
            print(
                f"  Group {i}: Kept idx {group['kept_index']}, Removed {group['removed_indices']}"
            )

    print(f"Final Dataset Size: {len(final_data)}")

    # Save the cleaned file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in final_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"--- Done. Clean data saved to {OUTPUT_FILE} ---")

    # Save duplicate report
    duplicate_report = {
        "summary": {
            "total_initial_rows": len(raw_data),
            "exact_duplicates_removed": exact_duplicates,
            "fuzzy_duplicates_removed": fuzzy_duplicates,
            "total_removed": exact_duplicates + fuzzy_duplicates,
            "final_dataset_size": len(final_data),
            "similarity_threshold": SIMILARITY_THRESHOLD,
        },
        "exact_duplicate_indices": exact_duplicate_indices,
        "fuzzy_duplicate_groups": fuzzy_duplicate_groups,
    }

    with open(DUPLICATE_REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(duplicate_report, f, indent=2, ensure_ascii=False)

    print(f"--- Duplicate report saved to {DUPLICATE_REPORT_FILE} ---")


if __name__ == "__main__":
    main()
