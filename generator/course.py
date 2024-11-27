import json
from openai import OpenAI
import time
import re
from .prompts import *
from utils.file_handler import ensure_vector_store_ready, cleanup_vector_store

class CourseGenerator:
    def __init__(self, client: OpenAI, model="gpt-4-0125-preview"):
        self.client = client
        self.model = model
        self.assistant_id = None
        self.thread_id = None

    def init_assistant(self, vector_store_id=None):
        assistant = self.client.beta.assistants.create(
            name="Course Generator",
            instructions="You are an expert course designer.",
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
        while True:
            run = self.client.beta.threads.runs.retrieve(thread_id=self.thread_id, run_id=run_id)
            if run.status == "completed":
                return run
            elif run.status in ["failed", "expired"]:
                raise Exception(f"Run failed: {run.last_error}")
            time.sleep(1)

    def _generate_step(self, prompt, context):
        """Run an individual step of the generation process."""
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=f"{prompt}\n\nContext: {json.dumps(context)}"
        )
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id
        )
        run = self.wait_for_run(run.id)

        messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
        for msg in messages.data:
            if msg.role == "assistant":
                content = msg.content[0].text.value.strip()
                print(f"Raw Assistant Response: {content}")

                match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
                if match:
                    json_content = match.group(1).strip()
                    try:
                        return json.loads(json_content)
                    except json.JSONDecodeError as e:
                        raise Exception(f"Error parsing JSON: {str(e)}\nExtracted JSON: {json_content}")

                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    raise Exception(f"Assistant response does not contain valid JSON: {content}")

        raise Exception("No valid response from assistant")

    def generate_course(self, user_input):
        course_info = self._generate_step(COURSE_INFO_PROMPT, context=user_input)
        structure = self._generate_step(STRUCTURE_PROMPT, context={**user_input, **course_info})

        for section in structure["sections"]:
            for lesson in section["lessons"]:
                # Generate lesson content
                lesson_content = self._generate_step(LESSON_PROMPT,
                                                  context={**user_input, **lesson})
                lesson.update(lesson_content)

                # Generate quiz for the lesson
                quiz = self._generate_step(QUIZ_PROMPT,
                                        context={**user_input, **lesson})
                lesson["quiz"] = quiz

        return {"course_info": course_info, "structure": structure}
