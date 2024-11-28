import json
from openai import OpenAI
import time
import re
import streamlit as st
from .prompts import *
from utils.file_handler import ensure_vector_store_ready, cleanup_vector_store

class CourseGenerator:
    def __init__(self, client: OpenAI, model="gpt-4-0125-preview"):
        self.client = client
        self.model = model
        self.assistant_id = None
        self.thread_id = None
        self.structure_prompt = STRUCTURE_PROMPT  # keep a modifiable copy

    def update_structure_prompt(self, extracted_content):
        """
        spice up the structure prompt with archaeological findings
        """
        context = ""

        if extracted_content["toc_found"]:
            context += f"""
REFERENCE TABLE OF CONTENTS:
--------------------------
{extracted_content['toc_content']}
--------------------------

Use this table of contents as primary structural guide while maintaining course requirements.
"""

        if extracted_content["content_preview"]:
            context += f"""
CONTENT PREVIEW:
--------------
{extracted_content['content_preview']}
--------------

Use this content to inform depth and complexity of lessons.
"""

        self.structure_prompt = f"{STRUCTURE_PROMPT}\n\n{context}"

    def init_assistant(self, vector_store_id=None):
        """initialize our AI teaching assistant"""
        assistant = self.client.beta.assistants.create(
            name="Course Generator",
            instructions="""You are an expert course designer with a talent for:
            1. Structuring knowledge effectively
            2. Adapting content to audience level
            3. Maintaining consistent tone and engagement
            4. Breaking complex topics into digestible lessons""",
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

    def wait_for_run(self, run_id):
        """wait for the assistant to finish cooking"""
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=run_id
            )
            if run.status == "completed":
                return run
            elif run.status in ["failed", "expired"]:
                raise Exception(f"Run failed: {run.last_error}")
            time.sleep(1)

    def extract_json_from_response(self, content):
        """
        archaeologist mode: dig through assistant's response for json
        handles both markdown and raw json formats
        """
        # first try: markdown code block
        match = re.search(r"```(?:json)?\n(.*?)\n```", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError as e:
                print(f"Failed to parse markdown json: {e}")

        # second try: raw json
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise Exception(f"No valid JSON found in response: {str(e)}\nRaw content: {content}")

    def _generate_step(self, prompt, context):
            """run a single generation step with SPICY logging"""
            st.write("🤖 preparing to generate...")

            # log what we're sending
            st.write("📤 sending to assistant:")
            st.expander("🔍 view prompt").code(prompt[:200] + "...", language="text")
            st.expander("📦 view context").code(str(context)[:200] + "...", language="json")

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
                    st.expander("🔍 view raw response").code(content[:200] + "...", language="text")

                    parsed = self.extract_json_from_response(content)
                    st.write("✅ successfully parsed JSON response")
                    return parsed

            raise Exception("no valid response from assistant")

    def generate_course(self, user_input):
        """
        the main course generation pipeline
        now with archaeology support!
        """
        # generate course info
        course_info = self._generate_step(COURSE_INFO_PROMPT, context=user_input)

        # generate structure (using potentially archaeologically enhanced prompt)
        structure = self._generate_step(
            self.structure_prompt,  # this might have our excavated content
            context={**user_input, **course_info}
        )

        # generate detailed lesson content
        for section in structure["sections"]:
            for lesson in section["lessons"]:
                lesson_content = self._generate_step(
                    LESSON_PROMPT,
                    context={**user_input, **lesson}
                )
                lesson.update(lesson_content)

        return {
            "course_info": course_info,
            "structure": structure
        }
