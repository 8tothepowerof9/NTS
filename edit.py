import asyncio
import json
from datetime import datetime
from pathlib import Path

import streamlit as st

# Set page config
st.set_page_config(page_title="Chapter Editor", page_icon="✏️", layout="wide")

st.markdown(
    """
    <style>
    .stTextArea textarea {
        font-family: 'Malgun Gothic', 'Arial Unicode MS', sans-serif;
    }
    .metadata-box {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
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


def create_empty_chapter(language):
    """Create an empty chapter template"""
    return {
        "url": "",
        "source_site": "",
        "language": language,
        "timestamp": datetime.now().isoformat(),
        "novel_title": "",
        "chapter_number": "",
        "content": "",
    }


def main():
    st.title("✏️ Chapter Editor")
    st.markdown("Edit aligned Korean and English chapters side by side")

    # Sidebar for file selection
    with st.sidebar:
        st.header("📂 File Selection")

        # Find all JSON files in output directory
        json_files = list(Path("output").rglob("*.json"))

        # Categorize files
        aligned_files = [
            f
            for f in json_files
            if "korean" not in f.name
            and "english" not in f.name
            and "indices" not in f.name
        ]
        korean_files = [f for f in json_files if "korean" in f.name.lower()]
        english_files = [f for f in json_files if "english" in f.name.lower()]

        # File mode selection
        mode = st.radio("Mode:", ["Load Aligned File", "Manual Pairing"])

        if mode == "Load Aligned File":
            if not aligned_files:
                st.warning("No aligned JSON files found in 'output' directory")
                return

            selected_file = st.selectbox(
                "Select aligned file:",
                aligned_files,
                format_func=lambda x: f"{x.parent.name}/{x.name}",
            )

            if st.button("🔄 Load File", type="primary"):
                data = load_json_file(selected_file)
                if data:
                    st.session_state.aligned_data = data
                    st.session_state.current_file = str(selected_file)
                    st.session_state.edited_data = [item.copy() for item in data]
                    st.session_state.mode = "aligned"
                    st.success(f"Loaded {len(data)} aligned chapters")

        else:  # Manual Pairing mode
            st.markdown("### Select Files")

            korean_file = None
            english_file = None

            if korean_files:
                korean_file = st.selectbox(
                    "Korean file:",
                    [None] + korean_files,
                    format_func=lambda x: (
                        "Select..." if x is None else f"{x.parent.name}/{x.name}"
                    ),
                )

            if english_files:
                english_file = st.selectbox(
                    "English file:",
                    [None] + english_files,
                    format_func=lambda x: (
                        "Select..." if x is None else f"{x.parent.name}/{x.name}"
                    ),
                )

            if st.button("🔄 Load for Pairing", type="primary"):
                if not korean_file and not english_file:
                    st.error("Please select at least one file")
                else:
                    korean_data = load_json_file(korean_file) if korean_file else []
                    english_data = load_json_file(english_file) if english_file else []

                    # Create aligned structure
                    max_len = max(len(korean_data), len(english_data))
                    aligned_data = []

                    for i in range(max_len):
                        korean_ch = (
                            korean_data[i]
                            if i < len(korean_data)
                            else create_empty_chapter("korean")
                        )
                        english_ch = (
                            english_data[i]
                            if i < len(english_data)
                            else create_empty_chapter("english")
                        )

                        aligned_data.append(
                            {"korean": korean_ch, "english": english_ch}
                        )

                    st.session_state.aligned_data = aligned_data
                    st.session_state.edited_data = [
                        item.copy() for item in aligned_data
                    ]
                    st.session_state.mode = "manual"
                    st.session_state.korean_file = (
                        str(korean_file) if korean_file else None
                    )
                    st.session_state.english_file = (
                        str(english_file) if english_file else None
                    )
                    st.success(f"Loaded {max_len} chapter pairs for manual editing")

    # Initialize session state
    if "aligned_data" not in st.session_state:
        st.info("👈 Please load files from the sidebar")
        return

    # Chapter navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 3, 2])

    with col1:
        if "current_chapter_idx" not in st.session_state:
            st.session_state.current_chapter_idx = 0

        total_chapters = len(st.session_state.edited_data)

        st.markdown(
            f"**Chapter {st.session_state.current_chapter_idx + 1} of {total_chapters}**"
        )

    with col2:
        chapter_idx = st.selectbox(
            "Jump to chapter:",
            range(total_chapters),
            index=st.session_state.current_chapter_idx,
            format_func=lambda x: f"Chapter {x + 1} - KR: {st.session_state.edited_data[x]['korean'].get('chapter_number', '?')} / EN: {st.session_state.edited_data[x]['english'].get('chapter_number', '?')}",
        )

        if chapter_idx != st.session_state.current_chapter_idx:
            st.session_state.current_chapter_idx = chapter_idx
            st.rerun()

    with col3:
        col_prev, col_next = st.columns(2)

        with col_prev:
            if st.button(
                "⬅️ Previous",
                use_container_width=True,
                disabled=st.session_state.current_chapter_idx == 0,
            ):
                st.session_state.current_chapter_idx -= 1
                st.rerun()

        with col_next:
            if st.button(
                "Next ➡️",
                use_container_width=True,
                disabled=st.session_state.current_chapter_idx >= total_chapters - 1,
            ):
                st.session_state.current_chapter_idx += 1
                st.rerun()

    st.markdown("---")

    # Get current chapter
    current_idx = st.session_state.current_chapter_idx
    chapter = st.session_state.edited_data[current_idx]

    # Display metadata
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Korean Chapter")
        korean = chapter["korean"]

        with st.container():
            st.markdown(
                f"""
            <div class="metadata-box">
                <b>Chapter:</b> {korean.get('chapter_number', 'N/A')}<br>
                <b>Novel:</b> {korean.get('novel_title', 'N/A')}<br>
                <b>Source:</b> {korean.get('source_site', 'N/A')}<br>
                <b>URL:</b> <a href="{korean.get('url', '#')}" target="_blank">Link</a>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col2:
        st.markdown("### English Chapter")
        english = chapter["english"]

        with st.container():
            st.markdown(
                f"""
            <div class="metadata-box">
                <b>Chapter:</b> {english.get('chapter_number', 'N/A')}<br>
                <b>Novel:</b> {english.get('novel_title', 'N/A')}<br>
                <b>Source:</b> {english.get('source_site', 'N/A')}<br>
                <b>URL:</b> <a href="{english.get('url', '#')}" target="_blank">Link</a>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Edit content
    st.markdown("---")
    st.markdown("### ✏️ Edit Content")

    col1, col2 = st.columns(2)

    with col1:
        korean_content = st.text_area(
            "Korean Content",
            value=korean.get("content", ""),
            height=600,
            key=f"korean_content_{current_idx}",
        )

        st.info(f"Characters: {len(korean_content)}")

    with col2:
        english_content = st.text_area(
            "English Content",
            value=english.get("content", ""),
            height=600,
            key=f"english_content_{current_idx}",
        )

        st.info(f"Characters: {len(english_content)}")

    # Update edited data
    st.session_state.edited_data[current_idx]["korean"]["content"] = korean_content
    st.session_state.edited_data[current_idx]["english"]["content"] = english_content

    # Save buttons
    st.markdown("---")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

    with col1:
        if st.button("💾 Save Changes", type="primary", use_container_width=True):
            if (
                st.session_state.get("mode") == "aligned"
                and "current_file" in st.session_state
            ):
                if save_json_file(
                    st.session_state.current_file, st.session_state.edited_data
                ):
                    st.success("✅ Changes saved successfully!")
                    st.balloons()
            elif st.session_state.get("mode") == "manual":
                # Save as aligned file
                novel_name = st.session_state.edited_data[0]["english"].get(
                    "novel_title", "Unknown"
                )
                output_dir = Path("output") / novel_name
                output_dir.mkdir(parents=True, exist_ok=True)
                aligned_file = output_dir / "aligned.json"

                if save_json_file(aligned_file, st.session_state.edited_data):
                    st.session_state.current_file = str(aligned_file)
                    st.session_state.mode = "aligned"
                    st.success(f"✅ Saved as aligned file: {aligned_file.name}")
                    st.balloons()

    with col2:
        if st.button("📥 Export as New File", use_container_width=True):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if "current_file" in st.session_state:
                original_path = Path(st.session_state.current_file)
                new_file = (
                    original_path.parent
                    / f"{original_path.stem}_edited_{timestamp}.json"
                )
            else:
                novel_name = st.session_state.edited_data[0]["english"].get(
                    "novel_title", "Unknown"
                )
                output_dir = Path("output") / novel_name
                output_dir.mkdir(parents=True, exist_ok=True)
                new_file = output_dir / f"aligned_edited_{timestamp}.json"

            if save_json_file(new_file, st.session_state.edited_data):
                st.success(f"✅ Exported to: {new_file.name}")

    with col3:
        if st.button("🔄 Reload Original", use_container_width=True):
            if (
                st.session_state.get("mode") == "aligned"
                and "current_file" in st.session_state
            ):
                data = load_json_file(st.session_state.current_file)
                if data:
                    st.session_state.edited_data = [item.copy() for item in data]
                    st.success("✅ Reloaded original data")
                    st.rerun()
            else:
                st.warning("Cannot reload in manual pairing mode")

    with col4:
        if st.button("➕ Add Chapter Pair", use_container_width=True):
            new_pair = {
                "korean": create_empty_chapter("korean"),
                "english": create_empty_chapter("english"),
            }
            st.session_state.edited_data.append(new_pair)
            st.session_state.current_chapter_idx = len(st.session_state.edited_data) - 1
            st.success("✅ Added new chapter pair")
            st.rerun()

    # Statistics
    with st.sidebar:
        st.markdown("---")
        st.header("📊 Statistics")

        total_korean_chars = sum(
            len(ch["korean"].get("content", "")) for ch in st.session_state.edited_data
        )
        total_english_chars = sum(
            len(ch["english"].get("content", "")) for ch in st.session_state.edited_data
        )

        st.metric("Total Chapters", len(st.session_state.edited_data))
        st.metric("Total Korean Characters", f"{total_korean_chars:,}")
        st.metric("Total English Characters", f"{total_english_chars:,}")

        st.markdown("---")
        st.markdown("**Current Chapter:**")
        st.metric("Korean Characters", len(korean_content))
        st.metric("English Characters", len(english_content))

        if korean_content and english_content:
            ratio = len(english_content) / len(korean_content)
            st.metric("EN/KR Ratio", f"{ratio:.2f}")


if __name__ == "__main__":
    main()
