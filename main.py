import json
from datetime import datetime
from pathlib import Path

import streamlit as st

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
    </style>
""",
    unsafe_allow_html=True,
)


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


def main():
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
            key=f"korean_content_{selected_chapter_idx}",  # Changed: unique key per chapter
        )

    with col2:
        st.markdown("#### English Content")
        english_content = st.text_area(
            "English Text",
            value=chapter["english"]["content"],
            height=600,
            key=f"english_content_{selected_chapter_idx}",  # Changed: unique key per chapter
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


if __name__ == "__main__":
    main()
