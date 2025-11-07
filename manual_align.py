import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

import streamlit as st


def load_chapters(file_path: Path) -> List[Dict]:
    """Load chapters from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_chapters(chapters: List[Dict]) -> Dict:
    """Merge multiple chapters into one by concatenating content."""
    if not chapters:
        return {}

    if len(chapters) == 1:
        return chapters[0]

    # Use first chapter as base
    merged = chapters[0].copy()

    # Concatenate content from all chapters
    merged_content = "\n\n".join([ch.get("content", "") for ch in chapters])
    merged["content"] = merged_content

    # Update chapter_number to show range
    chapter_numbers = [ch.get("chapter_number", "?") for ch in chapters]
    merged["chapter_number"] = f"{chapter_numbers[0]} - {chapter_numbers[-1]}"

    return merged


def save_aligned_chapters(
    alignments: List[Dict],
    english_chapters: List[Dict],
    korean_chapters: List[Dict],
    output_path: Path,
):
    """Save aligned and merged chapters to a JSON file."""
    aligned_data = []

    for alignment in alignments:
        # Get the actual chapters
        english_chs = [english_chapters[idx] for idx in alignment["english"]]
        korean_chs = [korean_chapters[idx] for idx in alignment["korean"]]

        # Merge if multiple chapters
        english_merged = merge_chapters(english_chs)
        korean_merged = merge_chapters(korean_chs)

        # Add to aligned data
        aligned_data.append({"korean": korean_merged, "english": english_merged})

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(aligned_data, f, ensure_ascii=False, indent=2)


def get_chapter_preview(chapter: Dict, lang: str, max_chars: int = 200) -> str:
    """Get a preview of the chapter content."""
    content = chapter.get("content", "")
    lines = content.split("\n")
    # Get first few non-empty lines
    preview_lines = [line.strip() for line in lines if line.strip()][:3]
    preview = " ".join(preview_lines)
    if len(preview) > max_chars:
        preview = preview[:max_chars] + "..."
    return preview


def main():
    st.set_page_config(page_title="Chapter Alignment Tool", layout="wide")
    st.title("📚 Chapter Alignment Tool")
    st.markdown("Align English and Korean novel chapters")

    # Sidebar for file selection and settings
    with st.sidebar:
        st.header("Settings")

        # File paths
        english_file = st.text_input(
            "English Chapters File",
            value="output/Stop, Friendly Fire!/chapters_english.json",
        )
        korean_file = st.text_input(
            "Korean Chapters File",
            value="output/Stop, Friendly Fire!/chapters_korean.json",
        )
        output_file = st.text_input(
            "Output Alignments File",
            value="output/Stop, Friendly Fire!/aligned.json",
        )

        # Load existing alignments if available
        if st.button("Load Chapters"):
            try:
                st.session_state.english_chapters = load_chapters(Path(english_file))
                st.session_state.korean_chapters = load_chapters(Path(korean_file))

                # Try to load existing alignment indices
                indices_path = (
                    Path(output_file).parent / f"{Path(output_file).stem}_indices.json"
                )
                if indices_path.exists():
                    with open(indices_path, "r", encoding="utf-8") as f:
                        st.session_state.alignments = json.load(f)
                else:
                    st.session_state.alignments = []

                st.success(
                    f"Loaded {len(st.session_state.english_chapters)} English and {len(st.session_state.korean_chapters)} Korean chapters"
                )
                st.session_state.current_alignment = {"english": [], "korean": []}
            except Exception as e:
                st.error(f"Error loading files: {e}")

    # Initialize session state
    if "english_chapters" not in st.session_state:
        st.session_state.english_chapters = []
    if "korean_chapters" not in st.session_state:
        st.session_state.korean_chapters = []
    if "alignments" not in st.session_state:
        st.session_state.alignments = []
    if "current_alignment" not in st.session_state:
        st.session_state.current_alignment = {"english": [], "korean": []}

    if not st.session_state.english_chapters or not st.session_state.korean_chapters:
        st.info("👈 Please load chapter files from the sidebar to begin")
        return

    # Main content area
    col1, col2 = st.columns(2)

    # English chapters selection
    with col1:
        st.header("English Chapters")

        # Show already aligned chapters
        aligned_english = set()
        for alignment in st.session_state.alignments:
            aligned_english.update(alignment["english"])

        # Filter options
        show_aligned = st.checkbox(
            "Show aligned chapters", value=False, key="show_aligned_en"
        )

        english_options = []
        for i, chapter in enumerate(st.session_state.english_chapters):
            is_aligned = i in aligned_english
            if show_aligned or not is_aligned:
                chapter_num = chapter.get("chapter_number", "Unknown")
                status = "✓" if is_aligned else "○"
                label = f"{status} {chapter_num}"
                english_options.append((i, label, chapter))

        selected_english = st.multiselect(
            "Select English chapters to align",
            options=[opt[0] for opt in english_options],
            format_func=lambda x: next(
                opt[1] for opt in english_options if opt[0] == x
            ),
            key="english_select",
        )

        # Show preview of selected chapters
        if selected_english:
            st.subheader("Preview")
            for idx in selected_english:
                chapter = st.session_state.english_chapters[idx]
                with st.expander(f"{chapter.get('chapter_number', 'Unknown')}"):
                    st.text(get_chapter_preview(chapter, "en"))

    # Korean chapters selection
    with col2:
        st.header("Korean Chapters")

        # Show already aligned chapters
        aligned_korean = set()
        for alignment in st.session_state.alignments:
            aligned_korean.update(alignment["korean"])

        show_aligned_kr = st.checkbox(
            "Show aligned chapters", value=False, key="show_aligned_kr"
        )

        korean_options = []
        for i, chapter in enumerate(st.session_state.korean_chapters):
            is_aligned = i in aligned_korean
            if show_aligned_kr or not is_aligned:
                chapter_num = chapter.get("chapter_number", "Unknown")
                status = "✓" if is_aligned else "○"
                label = f"{status} {chapter_num}"
                korean_options.append((i, label, chapter))

        selected_korean = st.multiselect(
            "Select Korean chapters to align",
            options=[opt[0] for opt in korean_options],
            format_func=lambda x: next(opt[1] for opt in korean_options if opt[0] == x),
            key="korean_select",
        )

        # Show preview of selected chapters
        if selected_korean:
            st.subheader("Preview")
            for idx in selected_korean:
                chapter = st.session_state.korean_chapters[idx]
                with st.expander(f"{chapter.get('chapter_number', 'Unknown')}"):
                    st.text(get_chapter_preview(chapter, "kr"))

    # Alignment controls
    st.divider()
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if st.button(
            "➕ Create Alignment",
            type="primary",
            disabled=not (selected_english and selected_korean),
        ):
            new_alignment = {
                "english": sorted(selected_english),
                "korean": sorted(selected_korean),
            }
            st.session_state.alignments.append(new_alignment)
            st.success(
                f"Created alignment: {len(selected_english)} EN ↔ {len(selected_korean)} KR"
            )
            st.rerun()

    with col2:
        if st.button("💾 Save Alignments", disabled=not st.session_state.alignments):
            # Save the aligned chapters
            save_aligned_chapters(
                st.session_state.alignments,
                st.session_state.english_chapters,
                st.session_state.korean_chapters,
                Path(output_file),
            )

    with col3:
        if st.button("🗑️ Clear Selection"):
            st.rerun()

    # Show existing alignments
    if st.session_state.alignments:
        st.divider()
        st.header("Current Alignments")

        for i, alignment in enumerate(st.session_state.alignments):
            with st.expander(
                f"Alignment {i+1}: {len(alignment['english'])} EN ↔ {len(alignment['korean'])} KR"
            ):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write("**English:**")
                    for idx in alignment["english"]:
                        chapter = st.session_state.english_chapters[idx]
                        ch_num = chapter.get("chapter_number", "Unknown")
                        st.write(f"- {ch_num}")

                with col2:
                    st.write("**Korean:**")
                    for idx in alignment["korean"]:
                        chapter = st.session_state.korean_chapters[idx]
                        ch_num = chapter.get("chapter_number", "Unknown")
                        st.write(f"- {ch_num}")

                with col3:
                    if st.button("Delete", key=f"del_{i}"):
                        st.session_state.alignments.pop(i)
                        st.rerun()

    # Statistics
    with st.sidebar:
        st.divider()
        st.header("Statistics")
        total_en = len(st.session_state.english_chapters)
        total_kr = len(st.session_state.korean_chapters)
        aligned_en_count = len(
            set(
                idx
                for alignment in st.session_state.alignments
                for idx in alignment["english"]
            )
        )
        aligned_kr_count = len(
            set(
                idx
                for alignment in st.session_state.alignments
                for idx in alignment["korean"]
            )
        )

        st.metric("Total Alignments", len(st.session_state.alignments))
        st.metric("English Aligned", f"{aligned_en_count}/{total_en}")
        st.metric("Korean Aligned", f"{aligned_kr_count}/{total_kr}")

        if total_en > 0:
            st.progress(aligned_en_count / total_en, text="English Progress")
        if total_kr > 0:
            st.progress(aligned_kr_count / total_kr, text="Korean Progress")


if __name__ == "__main__":
    main()
