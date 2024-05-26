import queue
import threading

import openai
from dotenv import load_dotenv

from playground.assistants_utils import EventHandler

load_dotenv()


class AssistantsAPI:
    def __init__(self):
        self.client = openai.OpenAI()
        self.actions_manager = None

    def create_thread(self):
        return self.client.beta.threads.create()

    def create_thread_message(self, thread_id, role, content, attachments=None):
        return self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role=role,
            content=content,
            attachments=attachments,
        )

    def create_assistant(
        self,
        name,
        instructions,
        model,
        tools,
        actions,
        response_format,
        temperature,
        top_p,
    ):
        assistant = self.client.beta.assistants.create(
            name=name,
            instructions=instructions,
            model=model,
            tools=tools + actions,
            response_format=response_format,
            temperature=temperature,
            top_p=top_p,
        )

        return assistant

    def run_stream(self, thread_id, assistant_id, event_handler):
        return self.client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant_id,
            event_handler=event_handler,
        )

    def list_assistants(self):
        assistants = self.client.beta.assistants.list(limit=100)
        return assistants

    def get_assistant_by_name(self, name):
        assistants = self.list_assistants()
        for assistant in assistants.data:
            if assistant.name.lower().startswith(name.lower()):
                return assistant
        return None

    def retrieve_assistant(self, assistant_id):
        try:
            assistant = self.client.beta.assistants.retrieve(assistant_id)
            return assistant
        except Exception:
            return None

    def update_assistant(
        self,
        assistant_name,
        assistant_id,
        assistant_instructions,
        assistant_model,
        assistant_tools,
        assistant_actions,
        assistant_resformat,
        assistant_temperature,
        assistant_top_p,
    ):
        assistant = self.client.beta.assistants.update(
            assistant_id,
            name=assistant_name,
            instructions=assistant_instructions,
            model=assistant_model,
            tools=assistant_tools + assistant_actions,
            response_format=assistant_resformat,
            temperature=assistant_temperature,
            top_p=assistant_top_p,
        )
        return assistant

    def delete_assistant(self, assistant_id):
        self.client.beta.assistants.delete(assistant_id)

    def upload_file(self, file, purpose="assistants"):
        return self.client.files.create(file=open(file, "rb"), purpose=purpose)

    def list_files(self, purpose="assistants"):
        return self.client.files.list(purpose=purpose)

    def retrieve_file(self, file_id):
        return self.client.files.retrieve(file_id)

    def delete_file(self, file_id):
        return self.client.files.delete(file_id)

    def call_assistant(self, thread, assistant_id, message):
        thread = self.create_thread()
        return self.call_assistant_with_thread(thread, assistant_id, message)

    def call_assistant_with_thread(self, thread, assistant_id, message):
        assistant = self.retrieve_assistant(assistant_id)
        output_queue = queue.Queue()
        eh = EventHandler(output_queue)
        thread_id = thread.id

        if assistant is None:
            msg = "Assistant not found."
            return msg

        def stream_worker(assistant_id, thread_id, event_handler):
            with self.run_stream(
                thread_id=thread_id,
                assistant_id=assistant_id,
                event_handler=event_handler,
            ) as stream:
                for text in stream.text_deltas:
                    output_queue.put(("text", text))

        # Start the initial stream
        thread_id = thread.id
        initial_thread = threading.Thread(
            target=stream_worker, args=(assistant.id, thread_id, eh)
        )
        initial_thread.start()
        reply = ""
        while initial_thread.is_alive() or not output_queue.empty():
            try:
                item_type, item_value = output_queue.get(timeout=0.1)
                if item_type == "text":
                    reply += item_value
                    # history[-1][1] = wrap_latex_with_markdown(history[-1][1])
                # yield history

            except queue.Empty:
                pass
        # history[-1][1] = wrap_latex_with_markdown(history[-1][1])
        # yield history
        # Final flush of images
        initial_thread.join()
        message = {"text": reply, "files": []}
        while len(eh.images) > 0:
            # history.append((None, (eh.images.pop(),)))
            # yield history
            message["files"].append(eh.images.pop())

        return message


api = AssistantsAPI()

# asss = api.list_assistants()
# for a in asss.data:
#     if a.name == "Sample Assistant":
#         api.delete_assistant(a.id)
