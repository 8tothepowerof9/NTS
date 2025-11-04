import asyncio
import json
from datetime import datetime
from pathlib import Path

import streamlit as st
from googletrans import Translator

# Set page config
st.set_page_config(page_title="Novel Translation Editor", page_icon="📚", layout="wide")

st.markdown(
    """
    <style>
    .stTextArea textarea {
        font-family: 'Malgun Gothic', 'Arial Unicode MS', sans-serif;
    }
    .chapter-title {
        font-size: 1.5em;
        font-weight: bold;
        margin-bottom: 1em;
    }
    .metadata {
        font-size: 0.9em;
        color: #666;
        margin-bottom: 1em;
    }
    .alignment-preview {
        border: 1px solid #ddd;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        background-color: #f9f9f9;
    }
    .chapter-info {
        font-weight: bold;
        color: #333;
    }
    </style>
""",
    unsafe_allow_html=True,
)


async def translate_text(text):
    async with Translator() as translator:
        result = await translator.translate(text, src="ko", dest="en")
        return result.text


def load_json_file(file_path):
    """Load JSON file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None


def save_json_file(file_path, data):
    """Save JSON file"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return False


def extract_chapters_by_language(data):
    """Extract and separate Korean and English chapters from paired data"""
    korean_chapters = []
    english_chapters = []

    for item in data:
        if "korean" in item:
            korean_chapters.append(item["korean"])
        if "english" in item:
            english_chapters.append(item["english"])

    return korean_chapters, english_chapters


def create_aligned_data(korean_chapters, english_chapters, alignment_map):
    """Create paired data based on alignment map"""
    aligned_data = []

    for ko_idx, en_idx in alignment_map.items():
        if ko_idx < len(korean_chapters) and en_idx < len(english_chapters):
            aligned_data.append(
                {"korean": korean_chapters[ko_idx], "english": english_chapters[en_idx]}
            )

    return aligned_data


def alignment_mode():
    """Manual alignment interface"""
    st.title("🔄 Manual Chapter Alignment")

    # File selection
    json_files = list(Path("output").glob("*.json"))

    if not json_files:
        st.warning("No JSON files found in the 'output' directory.")
        return

    selected_file = st.selectbox(
        "Select a novel file to realign:",
        json_files,
        format_func=lambda x: x.stem,
        key="align_file_select",
    )

    # Load data
    data = load_json_file(selected_file)

    if data is None:
        return

    # Extract chapters
    korean_chapters, english_chapters = extract_chapters_by_language(data)

    st.info(
        f"📚 Found {len(korean_chapters)} Korean chapters and {len(english_chapters)} English chapters"
    )

    # Initialize alignment state
    if "alignment_map" not in st.session_state or st.session_state.get(
        "align_file"
    ) != str(selected_file):
        st.session_state.alignment_map = {
            i: i for i in range(min(len(korean_chapters), len(english_chapters)))
        }
        st.session_state.align_file = str(selected_file)
        st.session_state.current_align_idx = 0
        st.session_state.preview_translations = {}

    # Current alignment index
    current_idx = st.session_state.current_align_idx

    st.markdown("---")

    # Progress
    total_to_align = len(korean_chapters)
    st.progress(
        current_idx / total_to_align if total_to_align > 0 else 0,
        text=f"Aligning: {current_idx + 1} / {total_to_align}",
    )

    if current_idx >= len(korean_chapters):
        st.success("✅ All chapters aligned! Review the alignment below.")

        # Show preview of all alignments
        st.markdown("### 📋 Alignment Preview")
        for ko_idx, en_idx in st.session_state.alignment_map.items():
            with st.expander(
                f"Korean Position {ko_idx + 1} (Ch {korean_chapters[ko_idx].get('chapter_number', 'N/A')}) ↔ "
                f"English Position {en_idx + 1} (Ch {english_chapters[en_idx].get('chapter_number', 'N/A')})"
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Korean:**")
                    st.markdown(
                        f"**Chapter:** {korean_chapters[ko_idx].get('chapter_number', 'N/A')}"
                    )
                    st.markdown(
                        f"**Title:** {korean_chapters[ko_idx].get('novel_title', 'N/A')}"
                    )
                    st.text_area(
                        "Preview",
                        korean_chapters[ko_idx].get("content", "")[:300] + "...",
                        height=100,
                        disabled=True,
                        key=f"preview_ko_{ko_idx}",
                    )
                with col2:
                    st.markdown("**English:**")
                    st.markdown(
                        f"**Chapter:** {english_chapters[en_idx].get('chapter_number', 'N/A')}"
                    )
                    st.markdown(
                        f"**Title:** {english_chapters[en_idx].get('novel_title', 'N/A')}"
                    )
                    st.text_area(
                        "Preview",
                        english_chapters[en_idx].get("content", "")[:300] + "...",
                        height=100,
                        disabled=True,
                        key=f"preview_en_{en_idx}",
                    )

        # Save aligned data
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "💾 Save Aligned Data", type="primary", use_container_width=True
            ):
                aligned_data = create_aligned_data(
                    korean_chapters, english_chapters, st.session_state.alignment_map
                )
                if save_json_file(selected_file, aligned_data):
                    st.success("✅ Aligned data saved successfully!")
                    st.balloons()

        with col2:
            if st.button("📥 Export as New File", use_container_width=True):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_file = (
                    selected_file.parent
                    / f"{selected_file.stem}_aligned_{timestamp}.json"
                )
                aligned_data = create_aligned_data(
                    korean_chapters, english_chapters, st.session_state.alignment_map
                )
                if save_json_file(new_file, aligned_data):
                    st.success(f"✅ Exported to: {new_file.name}")

        if st.button("🔄 Start Over", use_container_width=True):
            st.session_state.alignment_map = {
                i: i for i in range(min(len(korean_chapters), len(english_chapters)))
            }
            st.session_state.current_align_idx = 0
            st.session_state.preview_translations = {}
            st.rerun()

        return

    # Show current Korean chapter
    st.markdown(f"### Korean Chapter (Position {current_idx + 1})")
    korean_ch = korean_chapters[current_idx]

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"**Chapter Number:** {korean_ch.get('chapter_number', 'N/A')}")
        st.markdown(f"**Novel:** {korean_ch.get('novel_title', 'N/A')}")
        st.markdown(f"**Source:** {korean_ch.get('source_site', 'N/A')}")

    with col2:
        korean_preview = korean_ch.get("content", "")[:500]
        st.text_area(
            "Korean Content Preview",
            korean_preview + "...",
            height=200,
            disabled=True,
            key=f"ko_preview_{current_idx}",
        )

    # Automatic machine translation of Korean preview
    translation_key = f"ko_{current_idx}"

    # Check if translation exists for this chapter
    if translation_key not in st.session_state.preview_translations:
        with st.spinner("Translating Korean preview..."):
            try:
                translation = asyncio.run(translate_text(korean_preview))
                st.session_state.preview_translations[translation_key] = translation
            except Exception as e:
                st.session_state.preview_translations[translation_key] = (
                    f"[Translation Error: {str(e)}]"
                )

    # Display machine translation
    st.text_area(
        "Machine Translation Preview",
        st.session_state.preview_translations[translation_key],
        height=150,
        disabled=True,
        key=f"ko_translation_{current_idx}",
    )

    st.markdown("---")

    # Select matching English chapter
    st.markdown("### Select Matching English Chapter")

    # English chapter selection - using position order, not chapter number
    english_options = [
        f"Position {i+1} (Ch {en_ch.get('chapter_number', 'N/A')}): {en_ch.get('novel_title', 'N/A')[:50]}"
        for i, en_ch in enumerate(english_chapters)
    ]

    current_selection = st.session_state.alignment_map.get(current_idx, current_idx)
    if current_selection >= len(english_chapters):
        current_selection = 0

    selected_en_idx = st.selectbox(
        "Choose the English chapter that matches the Korean chapter above:",
        range(len(english_chapters)),
        index=current_selection,
        format_func=lambda x: english_options[x],
        key=f"en_select_{current_idx}",
    )

    # Show selected English chapter preview
    english_ch = english_chapters[selected_en_idx]

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"**Chapter Number:** {english_ch.get('chapter_number', 'N/A')}")
        st.markdown(f"**Novel:** {english_ch.get('novel_title', 'N/A')}")
        st.markdown(f"**Source:** {english_ch.get('source_site', 'N/A')}")

    with col2:
        st.text_area(
            "English Content Preview",
            english_ch.get("content", "")[:500] + "...",
            height=200,
            disabled=True,
            key=f"en_preview_{selected_en_idx}",
        )

    # Navigation buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⬅️ Previous", disabled=current_idx == 0, use_container_width=True):
            st.session_state.current_align_idx -= 1
            st.rerun()

    with col2:
        if st.button("✅ Confirm & Next", type="primary", use_container_width=True):
            st.session_state.alignment_map[current_idx] = selected_en_idx
            st.session_state.current_align_idx += 1
            st.rerun()

    with col3:
        if st.button("⏭️ Skip", use_container_width=True):
            st.session_state.current_align_idx += 1
            st.rerun()


def editor_mode():
    """Original editor interface"""
    st.title("📚 Novel Translation Editor")

    # File selection
    json_files = list(Path("output").glob("*.json"))

    if not json_files:
        st.warning("No JSON files found in the 'output' directory.")
        return

    selected_file = st.selectbox(
        "Select a novel file:", json_files, format_func=lambda x: x.stem
    )

    # Load data
    data = load_json_file(selected_file)

    if data is None:
        return

    # Initialize session state for edited data
    if "edited_data" not in st.session_state or "current_file" not in st.session_state:
        st.session_state.edited_data = data.copy()
        st.session_state.current_file = str(selected_file)

    # Reset if file changed
    if str(selected_file) != st.session_state.current_file:
        st.session_state.edited_data = data.copy()
        st.session_state.current_file = str(selected_file)

    # Chapter selection
    chapter_options = [f"Chapter {ch['korean']['chapter_number']}" for ch in data]
    selected_chapter_idx = st.selectbox(
        "Select a chapter:", range(len(data)), format_func=lambda x: chapter_options[x]
    )

    chapter = st.session_state.edited_data[selected_chapter_idx]

    # Display metadata
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🇰🇷 Korean Version")
        st.markdown(f"**Novel:** {chapter['korean']['novel_title']}")
        st.markdown(f"**Chapter:** {chapter['korean']['chapter_number']}")
        st.markdown(f"**Source:** {chapter['korean']['source_site']}")
        st.markdown(f"**Timestamp:** {chapter['korean']['timestamp']}")

    with col2:
        st.markdown("### 🇺🇸 English Version")
        st.markdown(f"**Novel:** {chapter['english']['novel_title']}")
        st.markdown(f"**Chapter:** {chapter['english']['chapter_number']}")
        st.markdown(f"**Source:** {chapter['english']['source_site']}")
        st.markdown(f"**Timestamp:** {chapter['english']['timestamp']}")

    st.markdown("---")

    # Edit content
    st.markdown("### ✏️ Edit Content")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Korean Content")
        korean_content = st.text_area(
            "Korean Text",
            value=chapter["korean"]["content"],
            height=600,
            key=f"korean_content_{selected_chapter_idx}",
        )

    with col2:
        st.markdown("#### English Content")
        english_content = st.text_area(
            "English Text",
            value=chapter["english"]["content"],
            height=600,
            key=f"english_content_{selected_chapter_idx}",
        )

    # Update edited data
    st.session_state.edited_data[selected_chapter_idx]["korean"][
        "content"
    ] = korean_content
    st.session_state.edited_data[selected_chapter_idx]["english"][
        "content"
    ] = english_content

    # Character count
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Korean character count: {len(korean_content or '')}")
    with col2:
        st.info(f"English character count: {len(english_content or '')}")

    # Save buttons
    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("💾 Save Changes", type="primary", use_container_width=True):
            if save_json_file(selected_file, st.session_state.edited_data):
                st.success("✅ Changes saved successfully!")
                st.balloons()

    with col2:
        if st.button("📥 Export as New File", use_container_width=True):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_file = (
                selected_file.parent / f"{selected_file.stem}_edited_{timestamp}.json"
            )
            if save_json_file(new_file, st.session_state.edited_data):
                st.success(f"✅ Exported to: {new_file.name}")

    # Statistics
    with st.expander("📊 Chapter Statistics"):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Korean Characters", len(chapter["korean"]["content"]))
            st.metric(
                "Korean Words (approx)", len(chapter["korean"]["content"].split())
            )
        with col2:
            st.metric("English Characters", len(chapter["english"]["content"]))
            st.metric("English Words", len(chapter["english"]["content"].split()))

    # Navigation URLs
    with st.expander("🔗 Navigation URLs"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Korean:**")
            st.markdown(f"- [Current URL]({chapter['korean']['url']})")
            if chapter["korean"]["prev_chapter_url"]:
                st.markdown(
                    f"- [Previous Chapter]({chapter['korean']['prev_chapter_url']})"
                )
            if chapter["korean"]["next_chapter_url"]:
                st.markdown(
                    f"- [Next Chapter]({chapter['korean']['next_chapter_url']})"
                )

        with col2:
            st.markdown("**English:**")
            st.markdown(f"- [Current URL]({chapter['english']['url']})")
            if chapter["english"]["prev_chapter_url"]:
                st.markdown(
                    f"- [Previous Chapter]({chapter['english']['prev_chapter_url']})"
                )
            if chapter["english"]["next_chapter_url"]:
                st.markdown(
                    f"- [Next Chapter]({chapter['english']['next_chapter_url']})"
                )


def main():
    # Sidebar for mode selection
    st.sidebar.title("⚙️ Mode Selection")
    mode = st.sidebar.radio(
        "Choose a mode:", ["📝 Editor", "🔄 Manual Alignment"], index=0
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📖 About")
    st.sidebar.info(
        "**Editor Mode**: Edit Korean and English translations\n\n"
        "**Manual Alignment**: Realign Korean and English chapters manually"
    )

    if mode == "📝 Editor":
        editor_mode()
    else:
        alignment_mode()


if __name__ == "__main__":
    main()
