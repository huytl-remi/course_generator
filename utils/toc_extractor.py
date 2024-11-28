from utils.file_handler import process_uploaded_file
import streamlit as st
import re

def extract_content_structure(file_content, file_type):
    """
    excavates structural knowledge from raw file content
    returns archaeologically significant findings
    """
    toc_pattern = re.compile(
        r'(?:table\s+of\s+contents?|contents?|index)',
        re.IGNORECASE
    )

    # first, let's try to find any ToC
    toc_section = None
    lines = file_content.split('\n')

    for i, line in enumerate(lines):
        if toc_pattern.search(line):
            # found potential ToC, grab next ~20 lines for analysis
            toc_section = '\n'.join(lines[i:i+20])
            break

    # get first ~5 pages worth of content (rough approximation)
    content_preview = '\n'.join(lines[:min(len(lines), 250)])  # ~50 lines per page

    return {
        "toc_found": bool(toc_section),
        "toc_content": toc_section if toc_section else None,
        "content_preview": content_preview
    }

def generate_structure_context(extracted_content):
    """formats our archaeological findings for the prompt"""
    st.write("🎨 formatting extracted content for prompt...")

    context = ""

    if extracted_content["toc_found"]:
        st.write("📑 including table of contents in prompt")
        context += f"""
REFERENCE TABLE OF CONTENTS FOUND:
--------------------------------
{extracted_content['toc_content']}
--------------------------------

Use this table of contents as primary guide for course structure.
"""

    if extracted_content["content_preview"]:
        st.write("📖 including content preview in prompt")
        context += f"""
CONTENT PREVIEW:
---------------
{extracted_content['content_preview']}
---------------

Use this content to inform depth and detail level.
"""

    st.code(context[:200] + "...", language="text")
    st.write("✨ prompt enhancement complete!")

    return context
