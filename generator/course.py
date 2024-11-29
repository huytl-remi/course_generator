import json
from openai import OpenAI
import time
import re
from .prompts import *
from utils.file_handler import ensure_vector_store_ready, cleanup_vector_store, process_files_for_content
import streamlit as st

class CourseGenerator:
    def __init__(self, client: OpenAI, model="gpt-4o-mini"):
        self.client = client
        self.model = model
        self.assistant_id = None
        self.thread_id = None
        self.raw_content = None
        self.structure = None

    def process_files(self, uploaded_files):
        """extract content from files"""
        st.write("🏺 beginning content extraction...")

        extracted = process_files_for_content(uploaded_files)
        if extracted:
            self.raw_content = extracted["content"]
            st.write("✨ content extraction complete!")
            return True

        st.warning("couldn't extract content from files")
        return False

    def init_assistant(self, vector_store_id=None):
        """set up our AI teaching assistant"""
        st.write("🤖 initializing AI assistant...")
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
        st.write("✅ assistant ready!")

    def extract_toc(self):
        """let AI find any structure in our content"""
        if not self.raw_content:
            st.error("no content to analyze!")
            return None

        if not self.thread_id:
            st.error("assistant not initialized!")
            return None

        st.write("🔍 analyzing content structure...")

        response = self._generate_step(
            TOC_EXTRACTION_PROMPT,
            {"content": self.raw_content}
        )

        if isinstance(response, str):
            found = response != "NO_STRUCTURE_FOUND"
            if found:
                st.write("🎯 found structure!")
                st.code(response, language="text")
                self.structure = response
                return response
            st.write("⚠️ no clear structure found")
            return None

        st.error("unexpected response format")
        return None

    def generate_course_info(self, user_input):
        """generate course info using any structure we found"""
        st.write("🎨 crafting course info...")

        context = {**user_input}
        if self.structure:
            context["extracted_structure"] = self.structure
        if self.raw_content:
            context["content_preview"] = self.raw_content

        course_info = self._generate_step(
            COURSE_INFO_PROMPT,
            context
        )

        st.write("✅ course info crafted!")
        return course_info

    def generate_sections(self, user_input, course_info):
        """generate course sections"""
        st.write("📑 structuring course sections...")

        context = {**user_input, **course_info}
        if self.structure:
            context["extracted_structure"] = self.structure
        if self.raw_content:
            context["content_preview"] = self.raw_content

        sections = self._generate_step(
            SECTION_GENERATION_PROMPT,
            context
        )

        st.write("✅ sections structured!")
        return sections

    def generate_lessons_for_section(self, user_input, course_info, section):
        """generate lessons for ONE spicy section"""
        st.write(f"📚 crafting lessons for: {section['title']}")

        context = {
            **user_input,
            **course_info,
            "section": section,
            # giving it some extra context about where we are in the course
            "current_section_time": section["estimated_time"],
            "total_lessons_needed": max(1, section["estimated_time"] // user_input["structure"]["lesson_length"])
        }

        if self.structure:
            context["extracted_structure"] = self.structure

        lessons = self._generate_step(
            LESSON_GENERATION_PROMPT,
            context
        )

        st.write(f"✨ generated {len(lessons['lessons'])} lessons!")
        return {
            "section_title": section["title"],
            "section_description": section["description"],
            "lessons": lessons["lessons"]
        }

    def _generate_step(self, prompt, context):
        """run a single generation step with spicy logging"""
        st.write("🤖 preparing to generate...")

        with st.expander("🔍 view prompt"):
            st.code(prompt, language="text")
        with st.expander("📦 view context"):
            st.code(json.dumps(context, indent=2), language="json")

        message = self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=f"{prompt}\n\nContext: {json.dumps(context)}"
        )

        st.write("⏳ waiting for response...")
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id
        )

        run = self.wait_for_run(run.id)

        messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
        for msg in messages.data:
            if msg.role == "assistant":
                content = msg.content[0].text.value.strip()
                st.write("📥 got response from assistant")
                with st.expander("🔍 view raw response"):
                    st.code(content, language="text")

                # ToC extraction might return just a string
                if prompt == TOC_EXTRACTION_PROMPT:
                    if content.startswith("{"):
                        return self.extract_json_from_response(content)
                    return content.strip()

                return self.extract_json_from_response(content)

        raise Exception("no valid response from assistant - this is AWKWARD")

    def wait_for_run(self, run_id):
        """patiently wait for our AI to cook up some content"""
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

    def extract_json_from_response(self, content):
        """parse json from response with MAXIMUM PREJUDICE"""
        st.write("🔍 attempting to parse response...")

        # first try: clean up obvious issues
        def clean_json_string(s):
            # fix common issues that break json
            fixes = [
                (r'(?<!\\)"(\w+)": ', r'"\1": '),  # fix unquoted property names
                (r',(\s*[}\]])', r'\1'),           # remove trailing commas
                (r'\\([^"])', r'\\\\\1'),          # escape backslashes
                (r'(?<!\\)\\(?!["\\])', r'\\\\'),  # escape remaining backslashes
            ]
            for pattern, replacement in fixes:
                s = re.sub(pattern, replacement, s)
            return s

        def extract_json_block(s):
            # try to find json block
            patterns = [
                r'```(?:json)?\n(.*?)\n```',  # markdown code block
                r'{[\s\S]*}',                 # raw json object
                r'\[[\s\S]*\]'                # raw json array
            ]
            for pattern in patterns:
                match = re.search(pattern, s, re.DOTALL)
                if match:
                    return match.group(1) if pattern.startswith('```') else match.group(0)
            return s

        try:
            # get potential json block
            json_str = extract_json_block(content)
            st.write("found potential json block:")
            st.code(json_str[:200] + "..." if len(json_str) > 200 else json_str)

            # clean it up
            cleaned = clean_json_string(json_str)

            # try to parse
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e1:
                st.write(f"💥 failed to parse cleaned json: {str(e1)}")
                st.write("attempting to parse original...")
                return json.loads(json_str)

        except json.JSONDecodeError as e:
            st.error("💥 json parsing failed!")
            st.write("problematic content:")
            st.code(content)

            # show exact error location
            error_msg = str(e)
            if "line" in error_msg and "column" in error_msg:
                line_no = int(re.search(r"line (\d+)", error_msg).group(1))
                col_no = int(re.search(r"column (\d+)", error_msg).group(1))

                lines = content.split("\n")
                st.write("error location:")
                for i in range(max(0, line_no-2), min(len(lines), line_no+1)):
                    prefix = ">>> " if i == line_no-1 else "    "
                    st.code(f"{prefix}{lines[i]}")
                    if i == line_no-1:
                        st.code(f"    {' '*(col_no-1)}^")

            raise Exception(f"no valid JSON found: {str(e)}")
