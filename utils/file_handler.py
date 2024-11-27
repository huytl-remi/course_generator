import tempfile
from pathlib import Path
from openai import OpenAI
import time

def process_uploaded_file(client: OpenAI, uploaded_files):
    vector_store = client.beta.vector_stores.create(name="Dynamic Vector Store")
    file_ids = []

    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(file.getvalue())
            file_path = tmp_file.name

        try:
            with open(file_path, 'rb') as file_data:
                uploaded_file = client.files.create(file=file_data, purpose="assistants")
                file_ids.append(uploaded_file.id)
        finally:
            Path(file_path).unlink(missing_ok=True)

    client.beta.vector_stores.file_batches.create_and_poll(vector_store_id=vector_store.id, file_ids=file_ids)
    ensure_vector_store_ready(client, vector_store.id)
    return vector_store.id

def ensure_vector_store_ready(client: OpenAI, vector_store_id):
    while True:
        vector_store = client.beta.vector_stores.retrieve(vector_store_id)
        if vector_store.status == "completed":
            return
        elif vector_store.status in ["failed", "expired"]:
            raise Exception(f"Vector store failed: {vector_store.status}")
        time.sleep(1)

def cleanup_vector_store(client: OpenAI, vector_store_id):
    try:
        client.beta.vector_stores.delete(vector_store_id)
    except Exception as e:
        print(f"Failed to delete vector store: {e}")
