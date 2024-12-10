"""Core course generation logic using OpenAI's API"""

import json
import time
import re
from .prompts import *
from utils.file_handler import ensure_vector_store_ready, cleanup_vector_store, process_files_for_content
import streamlit as st

class CourseGenerator:
    def __init__(self, client, model="gpt-4o-mini"):
        self.client = client
        self.model = model
        self.assistant_id = None
        self.thread_id = None
        self.raw_content = None
        self.structure = None

    def process_files(self, uploaded_files):
        """extract content from files"""
        try:
            extracted = process_files_for_content(uploaded_files)
            if not extracted:
                st.warning("no content found in files")
                return False

            if not extracted.get("content"):
                st.warning("content extraction returned empty result")
                return False

            self.raw_content = extracted["content"]
            return True

        except Exception as e:
            st.error(f"failed to process files: {str(e)}")
            # might wanna log the full traceback here
            return False

    def init_assistant(self, vector_store_id=None):
        """set up our AI teaching assistant"""
        assistant = self.client.beta.assistants.create(
            name="Course Generator",
            instructions="""You are an expert course designer with:
            1. Perfect content structure detection
            2. Audience adaptation skills
            3. Consistent tone maintenance
            4. Complex topic breakdown abilities""",
            model=self.model,
            tools=[{"type": "file_search"}]
        )
        self.assistant_id = assistant.id

        if vector_store_id:
            self.client.beta.assistants.update(
                assistant_id=self.assistant_id,
                tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
            )

        thread = self.client.beta.threads.create()
        self.thread_id = thread.id

    def extract_toc(self):
        """let AI find/generate structure"""
        if not self.thread_id:
            st.error("assistant not initialized!")
            return None

        # try extraction first
        response = self._generate_step(
            TOC_EXTRACTION_PROMPT,
            {
                "content": self.raw_content if self.raw_content else None,
                "category": st.session_state.user_input["category"],
                "familiarity": st.session_state.user_input["audience"]["familiarity"],
                "course_duration": st.session_state.user_input["structure"]["course_duration"]
            },
            requires_json=False  # raw first
        )

        # if we got a valid response (either raw TOC or json)
        if response:
            st.write("🎯 found/generated structure!")
            st.code(response if isinstance(response, str) else json.dumps(response, indent=2))
            self.structure = response
            return response

        st.write("⚠️ no structure found")
        return None

    def generate_course_info(self, user_input):
        """generate course info - returns markdown content"""
        st.write("🎨 crafting course info...")

        context = {**user_input}
        if self.structure:
            context["extracted_structure"] = self.structure
        if self.raw_content:
            context["content_preview"] = self.raw_content

        try:
            content = self._generate_step(
                COURSE_INFO_PROMPT,
                context,
                requires_json=False
            )

            # if we got raw markdown without tags, that's fine
            if not content.strip().startswith('<content>'):
                return content.strip()

            # if we got tags, extract the content
            content_match = re.search(r'<content>(.*?)</content>',
                                    content,
                                    re.DOTALL)
            if content_match:
                return content_match.group(1).strip()

            # if neither worked, show what we got
            st.warning("unexpected content format:")
            st.code(content)
            return content.strip()  # return it anyway

        except Exception as e:
            st.error(f"failed to generate course info: {str(e)}")
            raise

    def generate_sections(self, user_input, course_info):
        """generate course sections - needs json for UI"""
        # st.write("📑 structuring course sections...")
        context = {**user_input}
        if self.structure:
            context["extracted_structure"] = self.structure
        if self.raw_content:
            context["content_preview"] = self.raw_content

        sections = self._generate_step(
            SECTION_GENERATION_PROMPT,
            context,
            requires_json=True
        )
        # st.write("✅ sections structured!")
        return sections

    def generate_lesson_detail(self, user_input, course_info, section_title, lesson, custom_instruction=None):
        """generate detailed lesson content - returns markdown"""
        context = {
            **user_input,
            "section_title": section_title,
            "lesson": lesson,
            "word_count": user_input["structure"]["word_count"]  # NEW: pass through word count
        }
        if custom_instruction:
            context["custom_instruction"] = custom_instruction

        # WAIT - might wanna add word count validation
        content = self._generate_step(
            LESSON_DETAIL_PROMPT,
            context,
            requires_json=False
        )

        # ngl might be nice to check actual word count
        word_count = len(content.split())
        target = context["word_count"]
        if abs(word_count - target) > target * 0.2:  # 20% tolerance
            st.warning(f"⚠️ heads up: lesson length ({word_count} words) is pretty different from target ({target})")

        return content

    def generate_lessons_for_section(self, user_input, course_info, section):
        """generate lesson outlines - needs json for UI"""
        context = {
            **user_input,
            "section": section,
            "current_section_time": section["estimated_time"],
            "total_lessons_needed": max(1, section["estimated_time"] // user_input["structure"]["lesson_length"])
        }
        if self.structure:
            context["extracted_structure"] = self.structure

        lessons = self._generate_step(
            LESSON_GENERATION_PROMPT,
            context,
            requires_json=True
        )

        return {
            "section_title": section["title"],
            "section_description": section["description"],
            "lessons": lessons["lessons"]
        }

    def generate_quiz(self, lesson, lesson_detail):
        """generate quiz - needs json for UI"""
        context = {
            "lesson_title": lesson.get("title", "Untitled"),
            "content": lesson_detail
        }
        return self._generate_step(
            QUIZ_GENERATION_PROMPT,
            context,
            requires_json=True
        )

    def _generate_step(self, prompt, context, requires_json=False):
        """run a single generation step"""
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=f"{prompt}\n\nContext: {json.dumps(context)}"
        )

        progress_text = st.empty()
        progress_text.text("generating...")

        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id
        )

        run = self.wait_for_run(run.id)
        progress_text.empty()

        messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
        for msg in messages.data:
            if msg.role == "assistant":
                content = msg.content[0].text.value.strip()

                # TOC extraction is special - it can be raw text
                if prompt == TOC_EXTRACTION_PROMPT:
                    # if it looks like a TOC (has newlines and indentation)
                    if '\n' in content and any(line.startswith(' ') for line in content.split('\n')):
                        return content.strip()
                    # if not, try json (for generated TOC)
                    if requires_json:
                        return self._extract_json_from_response(content)

                # normal json/content handling
                if requires_json:
                    return self._extract_json_from_response(content)
                else:
                    return self._extract_content_from_response(content)

        raise Exception("no valid response from assistant")

    def wait_for_run(self, run_id):
        """wait for AI response"""
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=run_id
            )
            if run.status == "completed":
                return run
            elif run.status in ["failed", "expired"]:
                raise Exception(f"run failed: {run.last_error}")
            time.sleep(1)

    def _extract_json_from_response(self, content):
        """parse json from response (for UI-needed steps)"""
        # st.write("🔍 parsing json response...")

        def clean_json_string(s):
            fixes = [
                (r'(?<!\\)"(\w+)": ', r'"\1": '),  # fix unquoted props
                (r',(\s*[}\]])', r'\1'),           # fix trailing commas
                (r'\\([^"])', r'\\\\\1'),          # escape backslashes
                (r'(?<!\\)\\(?!["\\])', r'\\\\')   # escape remaining
            ]
            for pattern, replacement in fixes:
                s = re.sub(pattern, replacement, s)
            return s

        def extract_json_block(s):
            patterns = [
                r'```(?:json)?\n(.*?)\n```',  # markdown block
                r'{[\s\S]*}',                 # raw object
                r'\[[\s\S]*\]'                # raw array
            ]
            for pattern in patterns:
                match = re.search(pattern, s, re.DOTALL)
                if match:
                    return match.group(1) if pattern.startswith('```') else match.group(0)
            return s

        try:
            json_str = extract_json_block(content)
            cleaned = clean_json_string(json_str)

            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e1:
                st.write(f"💥 failed to parse cleaned json: {str(e1)}")
                st.write("attempting original...")
                return json.loads(json_str)

        except json.JSONDecodeError as e:
            st.error(f"💥 json parsing failed: {str(e)}")
            raise Exception(f"no valid json found: {str(e)}")

    def _extract_content_from_response(self, content):
        """extract and clean content"""
        # first clean any color formatting or special chars
        content = re.sub(r'#[A-Fa-f0-9]{6}', '', content)  # remove color codes

        # then normalize markdown
        content = self._normalize_markdown(content)

        # THEN do our normal content extraction
        if content.strip().startswith('#') or content.strip().startswith('-'):
            return content.strip()

        content_match = re.search(r'<content>(.*?)</content>',
                                content,
                                re.DOTALL)
        if content_match:
            return content_match.group(1).strip()

        if '\n' in content and any(line.startswith(('#', '-', '*')) for line in content.split('\n')):
            return content.strip()

        st.error("💥 couldn't parse content format!")
        st.code(content)
        raise Exception("no valid content found")

    def _normalize_markdown(self, content: str) -> str:
        """ensure consistent markdown formatting"""
        lines = content.split('\n')
        normalized = []

        for line in lines:
            # fix header formatting
            if line.startswith('#'):
                line = re.sub(r'^(#+)([^ ])', r'\1 \2', line)

            # fix emphasis markers - replace ** with proper markdown
            line = re.sub(r'\*\*(.*?)\*\*', r'**\1**', line)

            normalized.append(line)

        return '\n'.join(normalized)
