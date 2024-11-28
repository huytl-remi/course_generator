import re
import streamlit as st
from openai import OpenAI
from generator.course import CourseGenerator
from utils.file_handler import process_uploaded_file, cleanup_vector_store
from utils.toc_extractor import extract_content_structure

st.set_page_config(
    page_title="Course Generator",
    page_icon="📚",
    layout="wide"
)

# Spicy helper for content extraction
def process_files_for_content(uploaded_files):
    """
    archaeology mode: dig through files for structure
    now with PDF AWARENESS 🔍
    """
    import PyPDF2
    from io import BytesIO

    st.write("🔍 starting content archaeology...")

    for file in uploaded_files:
        st.write(f"📄 examining: {file.name}")

        try:
            if file.name.lower().endswith('.pdf'):
                st.write("🎯 PDF detected, using PyPDF2 for extraction...")
                pdf_bytes = BytesIO(file.getvalue())

                try:
                    pdf_reader = PyPDF2.PdfReader(pdf_bytes)

                    # Extract text from first few pages
                    content = ""
                    for i in range(min(5, len(pdf_reader.pages))):
                        content += pdf_reader.pages[i].extract_text() + "\n"

                    st.write(f"📚 extracted {len(content)} chars from first {min(5, len(pdf_reader.pages))} pages")

                    # look for actual table of contents
                    toc_pattern = re.compile(
                        r'(?:table\s+of\s+contents?|contents?|index|mục\s+lục)',  # added Vietnamese!
                        re.IGNORECASE
                    )

                    lines = content.split('\n')
                    toc_section = None

                    for i, line in enumerate(lines):
                        if toc_pattern.search(line):
                            st.write("🎯 Found potential ToC marker!")
                            # grab next chunk after ToC marker
                            toc_section = '\n'.join(lines[i:i+20])
                            st.write("preview of actual ToC content:")
                            st.code(toc_section[:200] + "...", language="text")
                            break

                    return {
                        "toc_found": bool(toc_section),
                        "toc_content": toc_section if toc_section else None,
                        "content_preview": content[:1000]  # first ~1000 chars
                    }

                except Exception as e:
                    st.write(f"💥 PDF processing error: {str(e)}")

            else:
                # handle text files with our existing logic
                content = file.getvalue().decode('utf-8', errors='ignore')
                st.write("📝 text file detected, scanning for structure...")

                extracted = extract_content_structure(content, file.name.split('.')[-1])
                if extracted["toc_found"] or extracted["content_preview"]:
                    return extracted

        except Exception as e:
            st.write(f"💥 unexpected error processing {file.name}: {str(e)}")
            continue

    st.warning("😅 couldn't extract meaningful structure from any files!")
    return None

# API key management in sidebar
st.sidebar.header("📝 Configuration")
api_key = st.sidebar.text_input(
    "OpenAI API Key",
    type="password",
    help="Enter your OpenAI API key",
    key="api_key_input"
)

if st.sidebar.button("Save API Key"):
    if api_key:
        st.session_state['OPENAI_API_KEY'] = api_key
        st.sidebar.success("API key saved!")
    else:
        st.sidebar.error("Please enter an API key")

# Main app
st.title("📚 Course Generator")
st.write("Create structured courses with AI assistance")

if 'OPENAI_API_KEY' not in st.session_state:
    st.warning("Please configure your OpenAI API key in the sidebar to continue")
else:
    client = OpenAI(api_key=st.session_state['OPENAI_API_KEY'])

    with st.form("course_input"):
        # Course Basics
        col1, col2 = st.columns(2)
        with col1:
            category = st.text_input(
                "Category",
                help="Enter the course category",
                key="category_input"
            )

        with col2:
            tone = st.selectbox(
                "Tone",
                options=["Friendly", "Professional", "Informative", "Engaging",
                        "Casual", "Humorous", "Storytelling", "Analytical", "Inspiring"],
                help="Select the teaching style and tone"
            )

        # Language input
        language = st.text_input(
            "Course Language",
            help="Enter the language for course content generation"
        )

        # Learner Demographics
        col3, col4, col5 = st.columns(3)
        with col3:
            start_age = st.number_input("Start Age", min_value=5, max_value=100, value=18)
        with col4:
            end_age = st.number_input("End Age", min_value=5, max_value=100, value=65)
        with col5:
            familiarity = st.selectbox(
                "Familiarity Level",
                options=["Beginner", "Intermediate", "Advanced"],
                help="Select the target audience's experience level"
            )

        # Course Structure
        col6, col7 = st.columns(2)
        with col6:
            course_duration = st.number_input(
                "Course Duration (hours)",
                min_value=1,
                max_value=40,
                value=10,
                help="Total course duration in hours"
            )
        with col7:
            lesson_length = st.number_input(
                "Lesson Length (minutes)",
                min_value=15,
                max_value=120,
                value=45,
                help="Duration of each lesson in minutes"
            )

        # Detailed Inputs
        needs_interests = st.text_area(
            "Needs and Interests",
            help="Describe the specific needs and interests of your target audience"
        )

        main_content = st.text_area(
            "Main Content",
            help="Outline the primary topics and content to be covered (optional if reference materials provided)"
        )

        # File upload
        uploaded_files = st.file_uploader(
            "Upload reference materials (optional if main content provided)",
            type=["pdf", "txt", "md", "docx"],
            accept_multiple_files=True,
            help="Documents to use as reference material"
        )

        generate = st.form_submit_button("Generate Course")

    if generate:
        if not (main_content or uploaded_files):
            st.error("Please either provide main content or upload reference materials")
        elif not all([language, needs_interests]):
            st.error("Please fill in all required fields (language and needs/interests)")
        else:
            try:
                generator = CourseGenerator(client, model="gpt-4-0125-preview")
                vector_store_id = None
                extracted_content = None

                # ARCHAEOLOGY MODE: if no main content but files exist
                if not main_content and uploaded_files:
                    with st.spinner("Analyzing reference materials for structure..."):
                        extracted_content = process_files_for_content(uploaded_files)
                        if not extracted_content:
                            st.warning("Couldn't extract structure from files. Using them as reference only.")

                # process files for vector store regardless
                if uploaded_files:
                    with st.spinner("Processing reference material..."):
                        vector_store_id = process_uploaded_file(client, uploaded_files)

                generator.init_assistant(vector_store_id)

                # if we found structure in files, update the prompt
                if extracted_content:
                    generator.update_structure_prompt(extracted_content)

                progress = st.progress(0)
                status = st.empty()
                status.text("Generating course...")

                course = generator.generate_course({
                    "language": language,
                    "category": category,
                    "tone": tone,
                    "audience": {
                        "age_range": {"start": start_age, "end": end_age},
                        "familiarity": familiarity
                    },
                    "structure": {
                        "course_duration": course_duration,
                        "lesson_length": lesson_length
                    },
                    "content": {
                        "needs_interests": needs_interests,
                        "main_content": main_content
                    }
                })

                progress.progress(100)
                st.success("Course generated successfully!")

                # Display the course (keeping the same display logic)
                st.header(course["course_info"]["course_name"])
                st.write(course["course_info"]["description"])

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Prerequisites")
                    st.write(course["course_info"]["prerequisites"])

                with col2:
                    st.subheader("Learning Outcomes")
                    for outcome in course["course_info"]["learning_outcomes"]:
                        st.write(f"- {outcome}")

                st.subheader("Course Structure")
                for section in course["structure"]["sections"]:
                    with st.expander(f"📘 {section['title']}"):
                        st.write(section["description"])

                        for lesson in section["lessons"]:
                            st.write(f"### 📝 {lesson['title']}")
                            st.write(f"Duration: {lesson['duration']} minutes")
                            st.write("#### Key Points")
                            for point in lesson["lesson_content"]["key_points"]:
                                st.write(f"- **{point['concept']}:** {point['explanation']}")

                if st.button("Download Course JSON"):
                    st.download_button(
                        "Download",
                        data=str(course),
                        file_name="course.json",
                        mime="application/json"
                    )

            except Exception as e:
                st.error(f"Error generating course: {str(e)}")

            finally:
                if vector_store_id:
                    cleanup_vector_store(client, vector_store_id)
