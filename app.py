"""Main Streamlit application for course generation"""

import re
import streamlit as st
from openai import OpenAI
from generator.course import CourseGenerator
from utils.file_handler import process_uploaded_file, cleanup_vector_store
import json

st.set_page_config(
    page_title="Course Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'generation_stage' not in st.session_state:
    st.session_state.generation_stage = 'input'
    # stages: input -> toc -> course_info -> sections -> lessons -> complete

# --- UI COMPONENTS --- #
def show_course_info(info: str):
    """Display course overview from markdown content"""
    st.markdown(info)

def show_sections(sections):
    st.subheader("course structure")
    total_time = sum(section["estimated_time"] for section in sections["sections"])
    st.write(f"total estimated time: {total_time} minutes ({total_time/60:.1f} hours)")

    for i, section in enumerate(sections["sections"], 1):
        st.markdown(f"""
        ## {i}. {section['title']}
        *{section['description']}*

        estimated time: {section['estimated_time']} minutes
        """)

        for j, lesson in enumerate(section["lessons"], 1):
            detail_key = f"lesson_detail_{section['title']}_{lesson['title']}"

            st.markdown(f"""
            ---
            ### {i}.{j} {lesson['title']}
            *{lesson['duration']} minutes*

            {lesson['brief']}
            """)

            if detail_key in st.session_state:
                show_lesson_detail(st.session_state[detail_key])
            else:
                instruction_key = f"instruction_{detail_key}"
                custom_instruction = st.text_area(
                    "your special instructions (optional):",
                    help="got specific ideas? tell me what to focus on",
                    key=instruction_key,
                    placeholder="e.g. 'focus on real-world applications'"
                )

                if st.button("🚀 generate lesson", key=f"gen_{detail_key}"):
                    with st.spinner("brewing knowledge... 🧪"):
                        detail = st.session_state.generator.generate_lesson_detail(
                            st.session_state.user_input,
                            st.session_state.course_info,
                            section["title"],
                            lesson,
                            st.session_state.get(instruction_key)
                        )
                        st.session_state[detail_key] = detail
                        st.rerun()

        st.markdown("---")

def show_lessons(all_lessons):
    st.subheader("Detailed Course Content")

    for section in all_lessons:
        with st.expander(f"📘 {section['section_title']}"):
            st.write(section["section_description"])

            for lesson in section["lessons"]:
                st.write(f"### 📝 {lesson['title']}")
                st.write(f"Duration: {lesson['duration']} minutes")

                st.write("#### Key Points")
                for point in lesson["lesson_content"]["key_points"]:
                    st.write(f"- **{point['concept']}:** {point['explanation']}")

                st.write("#### Examples")
                for example in lesson["lesson_content"]["examples"]:
                    st.write(f"- {example}")

                st.write("#### Key Takeaways")
                for takeaway in lesson["lesson_content"]["takeaways"]:
                    st.write(f"- {takeaway}")

def show_section_lessons(section_lessons):
    """show lesson outlines for current section"""
    st.write("#### Lesson Outlines")

    for lesson in section_lessons["lessons"]:
        with st.expander(f"📝 {lesson['title']} ({lesson['duration']} mins)"):
            st.write(lesson["brief"])

            # store details in session state if we have them
            lesson_key = f"lesson_detail_{section_lessons['section_title']}_{lesson['title']}"

            if lesson_key in st.session_state:
                detail = st.session_state[lesson_key]
                show_lesson_detail(detail)
            else:
                if st.button("Generate Full Lesson", key=f"gen_{lesson_key}"):
                    # generate details when requested
                    detail = st.session_state.generator.generate_lesson_detail(
                        st.session_state.user_input,
                        st.session_state.course_info,
                        section_lessons['section_title'],
                        lesson
                    )
                    st.session_state[lesson_key] = detail
                    show_lesson_detail(detail)

def show_quiz(quiz, answers_key):
    """display quiz with state management"""
    if answers_key not in st.session_state:
        # init answer state
        st.session_state[answers_key] = {
            f"q{i}": None for i in range(len(quiz["questions"]))
        }

    answers = st.session_state[answers_key]
    all_correct = True

    # progress header
    total = len(quiz["questions"])
    answered = sum(1 for v in answers.values() if v is not None)
    correct = sum(1 for v in answers.values() if v is True)

    st.write(f"### quiz progress: {correct}/{total} correct")
    st.progress(correct/total)

    # show each question
    for i, q in enumerate(quiz["questions"]):
        # question state indicator
        state = "🤔" if answers[f"q{i}"] is None else (
                "✅" if answers[f"q{i}"] else "❌")

        st.write(f"\n#### Question {i+1} {state}")

        if q["type"] == "multi_choice":
            choice = st.radio(
                q["question"],
                q["options"],
                key=f"radio_{answers_key}_{i}"
            )

            # check answer button
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("check", key=f"check_{answers_key}_{i}"):
                    is_correct = q["options"].index(choice) == q["correct"]
                    answers[f"q{i}"] = is_correct
                    if is_correct:
                        st.success("nice one! 🎉")
                    else:
                        st.error("not quite - try again!")
                        all_correct = False

        else:  # true/false
            answer = st.radio(
                q["statement"],
                ["True", "False"],
                key=f"radio_{answers_key}_{i}"
            )

            # check answer button
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("check", key=f"check_{answers_key}_{i}"):
                    is_correct = (answer == "True") == q["correct"]
                    answers[f"q{i}"] = is_correct
                    if is_correct:
                        st.success("spot on! 🎯")
                    else:
                        st.error("nope - give it another shot!")
                        all_correct = False

    # quiz completion
    if all(v is not None for v in answers.values()):
        if all_correct:
            st.balloons()
            st.success("you've mastered this lesson! 🎓")
        else:
            st.info("almost there! fix those red questions and try again 💪")
            if st.button("reset quiz"):
                for k in answers:
                    answers[k] = None

def show_lesson_detail(detail: str):
    """Show the lesson content with word count and quiz"""
    # NEW: add word count info before content
    word_count = len(detail.split())
    target = st.session_state.user_input["structure"]["word_count"]
    st.text(f"Words: {word_count} / {target} target")

    # existing content display
    st.markdown(detail)

    # existing quiz section
    lesson_id = str(hash(detail))
    quiz_key = f"quiz_{lesson_id}"
    with st.expander("🧠 knowledge check", expanded=False):
        if quiz_key in st.session_state:
            show_quiz(st.session_state[quiz_key], f"answers_{quiz_key}")
        else:
            if st.button("🎯 cook up a quiz", key=f"gen_quiz_{quiz_key}"):
                with st.spinner("brewing brain teasers... 🧩"):
                    lesson_context = {
                        "title": _extract_title(detail),
                    }
                    quiz = st.session_state.generator.generate_quiz(
                        lesson_context,
                        detail
                    )
                    st.session_state[quiz_key] = quiz
                    st.rerun()

def _extract_title(markdown: str) -> str:
    """Helper to get first h1 from markdown"""
    if match := re.search(r'^#\s+(.+)$', markdown, re.MULTILINE):
        return match.group(1)
    return 'current lesson'  # fallback

# Sidebar for configuration
with st.sidebar:
    st.header("📝 Configuration")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Enter your OpenAI API key",
        key="api_key_input"
    )

    if st.button("Save API Key"):
        if api_key:
            st.session_state['OPENAI_API_KEY'] = api_key
            st.success("API key saved!")
        else:
            st.error("Please enter an API key")

    # show generation progress
    if 'generation_stage' in st.session_state:
        st.header("Generation Progress")
        stages = ['input', 'toc', 'course_info', 'sections', 'lessons', 'complete']
        current = stages.index(st.session_state.generation_stage)

        progress = st.progress(current / (len(stages) - 1))
        st.caption(f"Stage: {st.session_state.generation_stage}")

if 'OPENAI_API_KEY' not in st.session_state:
    st.warning("Please configure your OpenAI API key in the sidebar to continue")
else:
    client = OpenAI(api_key=st.session_state['OPENAI_API_KEY'])

    if 'course_info' in st.session_state:
        show_course_info(st.session_state.course_info)

    if st.session_state.generation_stage == 'input':
        # predefined categories OUTSIDE the form
        categories = [
            "Default", "Mathematics", "Physics", "Chemistry", "Biology",
            "Computer Science", "Engineering", "Data Science",
            "Visual Arts", "Music", "Literature", "Creative Writing",
            "Photography", "Film & Media", "Design",
            "English", "Spanish", "Mandarin", "Japanese",
            "French", "German", "Arabic",
            "Business", "Marketing", "Finance", "Project Management",
            "Leadership", "Communication", "Entrepreneurship",
            "Philosophy", "Psychology", "History", "Political Science",
            "Environmental Studies", "Health & Wellness",
            "Personal Development", "Other"
        ]

        category = st.selectbox(
            "Category",
            options=categories,
            help="Select the course category"
        )

        # show "Other" field if they pick that option
        if category == "Other":
            custom_category = st.text_input(
                "Custom Category",
                help="Enter your custom course category"
            )

        # now start the form
        with st.form("course_input"):

            tone = st.selectbox(
                "Tone",
                options=["Professional", "Friendly", "Informative", "Engaging",
                        "Casual", "Humorous", "Storytelling", "Analytical", "Inspiring"],
                help="Select the teaching style and tone"
            )

            language = st.text_input(
                "Course Language",
                help="Enter the language for course content generation"
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                start_age = st.number_input("Start Age", min_value=5, max_value=100, value=18)
            with col2:
                end_age = st.number_input("End Age", min_value=5, max_value=100, value=65)
            with col3:
                familiarity = st.selectbox(
                    "Familiarity Level",
                    options=["Beginner", "Intermediate", "Advanced"]
                )

            col4, col5 = st.columns(2)
            with col4:
                course_duration = st.number_input(
                    "Course Duration (hours)",
                    min_value=1,
                    max_value=40,
                    value=10
                )
            with col5:
                lesson_length = st.number_input(
                    "Lesson Length (minutes)",
                    min_value=15,
                    max_value=120,
                    value=45
                )
            col6, _ = st.columns([1, 1])  # using columns for layout consistency
            with col6:
                word_count = st.number_input(
                    "Words per Lesson",
                    min_value=100,
                    max_value=5000,
                    value=500,
                    help="Target word count for each lesson's content"
                )

            main_content = st.text_area(
                "Main Content",
                help="Outline the primary topics and content to be covered (optional if reference materials provided)"
            )

            uploaded_files = st.file_uploader(
                "Upload reference materials (optional if main content provided)",
                type=["pdf", "txt", "md", "docx"],
                accept_multiple_files=True
            )

            submitted = st.form_submit_button("Start Generation")

        if submitted:
            # validate required inputs
            missing = []
            if not language:
                missing.append("language")
            if category == "Other" and not custom_category:
                missing.append("custom category")

            if missing:
                st.error(f"Please fill in: {', '.join(missing)}")
            else:
                final_category = custom_category if category == "Other" else category
                st.session_state.user_input = {
                    "language": language,
                    "category": final_category,
                    "tone": tone,
                    "audience": {
                        "age_range": {"start": start_age, "end": end_age},
                        "familiarity": familiarity
                    },
                    "structure": {
                        "course_duration": course_duration,
                        "lesson_length": lesson_length,
                        "word_count": word_count
                    },
                    "content": {
                        "main_content": main_content
                    }
                }
                st.session_state.uploaded_files = uploaded_files
                st.session_state.generation_stage = 'toc'
                st.rerun()

    elif st.session_state.generation_stage == 'toc':
        st.write("🔍 analyzing content structure...")

        try:
            # initialize generator
            generator = CourseGenerator(client)

            # FIRST: process files if we have them
            content_found = False
            if st.session_state.uploaded_files:
                content_found = generator.process_files(st.session_state.uploaded_files)

            # SECOND: set up vector store if needed
            vector_store_id = None
            if st.session_state.uploaded_files:
                vector_store_id = process_uploaded_file(client, st.session_state.uploaded_files)

            # THIRD: initialize assistant with vector store
            generator.init_assistant(vector_store_id)

            # FINALLY: try to extract ToC if we found content
            if content_found:
                raw_toc = generator.extract_toc()
                if raw_toc:
                    st.session_state.raw_toc = raw_toc

            # store generator and move on
            st.session_state.generator = generator
            st.session_state.generation_stage = 'course_info'
            st.rerun()

        except Exception as e:
            st.error(f"error during content analysis: {str(e)}")
            if 'vector_store_id' in locals():
                cleanup_vector_store(client, vector_store_id)

    elif st.session_state.generation_stage == 'course_info':
        st.write("🎨 generating course information...")

        try:
            course_info = st.session_state.generator.generate_course_info(
                st.session_state.user_input
            )
            st.session_state.course_info = course_info  # now stores markdown string

            if st.button("✨ Generate Course Structure"):
                st.session_state.generation_stage = 'sections'
                st.rerun()

        except Exception as e:
            st.error(f"Error generating course info: {str(e)}")

    elif st.session_state.generation_stage == 'sections':
        # st.write("📑 generating course structure...")

        try:
            # Only generate sections if not already in session state
            if 'sections' not in st.session_state:
                sections = st.session_state.generator.generate_sections(
                    st.session_state.user_input,
                    st.session_state.course_info
                )
                st.session_state.sections = sections

            show_sections(st.session_state.sections)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("👎 Regenerate Structure"):
                    del st.session_state.sections
                    st.rerun()

        except Exception as e:
            st.error(f"Error generating sections: {str(e)}")

    elif st.session_state.generation_stage == 'lessons':
            if 'current_section_index' not in st.session_state:
                st.session_state.current_section_index = 0
                st.session_state.generated_lessons = []

            sections = st.session_state.sections["sections"]
            current_section = sections[st.session_state.current_section_index]

            st.subheader(f"Generating Lessons for Section {st.session_state.current_section_index + 1}/{len(sections)}")
            st.write(f"📘 {current_section['title']}")
            st.write(current_section['description'])

            try:
                if 'current_section_lessons' not in st.session_state:
                    # generate lessons for this section
                    section_lessons = st.session_state.generator.generate_lessons_for_section(
                        st.session_state.user_input,
                        st.session_state.course_info,
                        current_section
                    )
                    st.session_state.current_section_lessons = section_lessons

                # show the generated lessons
                show_section_lessons(st.session_state.current_section_lessons)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👎 Regenerate These Lessons"):
                        del st.session_state.current_section_lessons
                        st.rerun()

                with col2:
                    if st.button("👍 Keep These Lessons"):
                        # save these lessons
                        st.session_state.generated_lessons.append(
                            st.session_state.current_section_lessons
                        )

                        # move to next section or finish
                        if st.session_state.current_section_index + 1 < len(sections):
                            st.session_state.current_section_index += 1
                            del st.session_state.current_section_lessons
                        else:
                            st.session_state.lessons = st.session_state.generated_lessons
                            st.session_state.generation_stage = 'complete'
                        st.rerun()

            except Exception as e:
                st.error(f"Error generating lessons: {str(e)}")

    elif st.session_state.generation_stage == 'complete':
        st.success("🎉 Course generation complete!")

        show_course_info(st.session_state.course_info)
        show_sections(st.session_state.sections)
        show_lessons(st.session_state.lessons)

        if st.button("🔄 Start New Course"):
            for key in list(st.session_state.keys()):
                if key != 'OPENAI_API_KEY':
                    del st.session_state[key]
            st.session_state.generation_stage = 'input'
            st.rerun()
