import streamlit as st
from openai import OpenAI
from generator.course import CourseGenerator
from utils.file_handler import process_uploaded_file, cleanup_vector_store

st.set_page_config(
    page_title="Course Generator",
    page_icon="📚",
    layout="wide"
)

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
        language = st.text_input(
            "Course Language",
            help="Enter the language for course content generation"
        )

        difficulty = st.selectbox(
            "Course Difficulty",
            options=[
                "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5",
                "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10",
                "Grade 11", "Grade 12", "College", "Professional"
            ],
            help="Select the target difficulty level"
        )

        prerequisites = st.text_area(
            "What should learners know before starting?",
            help="List any required knowledge or skills"
        )

        outcomes = st.text_area(
            "What will learners be able to do after?",
            help="Describe the expected learning outcomes"
        )

        uploaded_files = st.file_uploader(
            "Upload reference materials (optional)",
            type=["pdf", "txt", "md", "docx"],
            accept_multiple_files=True,
            help="Documents to use as reference material"
        )

        generate = st.form_submit_button("Generate Course")

    if generate:
        if not prerequisites or not outcomes or not language:
            st.error("Please fill in all required fields (language, prerequisites, and outcomes)")
        else:
            try:
                generator = CourseGenerator(client, model="gpt-4-0125-preview")
                vector_store_id = None

                if uploaded_files:
                    with st.spinner("Processing reference material..."):
                        vector_store_id = process_uploaded_file(client, uploaded_files)

                generator.init_assistant(vector_store_id)

                progress = st.progress(0)
                status = st.empty()
                status.text("Generating course...")

                course = generator.generate_course({
                    "language": language,
                    "difficulty": difficulty,
                    "prerequisites": prerequisites,
                    "outcomes": outcomes
                })
                progress.progress(100)

                st.success("Course generated successfully!")
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

                            st.write("#### Quiz")
                            for idx, quiz in enumerate(lesson["quiz"]["questions"], 1):
                                st.write(f"**Q{idx}: {quiz['question']}**")
                                if quiz["type"] == "multiple_choice":
                                    for choice in quiz["choices"]:
                                        st.write(f"- {'✅' if choice['is_correct'] else '❌'} {choice['text']}")
                                else:  # true_false
                                    st.write(f"Answer: {'True ✅' if quiz['choices'][0]['is_correct'] else 'False ❌'}")
                                st.write(f"*Explanation: {quiz['explanation']}*")

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
