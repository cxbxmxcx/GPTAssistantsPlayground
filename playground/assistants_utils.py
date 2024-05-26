import datetime
import json
import os

import openai
from dotenv import load_dotenv
from openai import AssistantEventHandler
from typing_extensions import override

from playground.actions_manager import ActionsManager

load_dotenv()

# OpenAI client initialization
client = openai.OpenAI()

OUTPUT_FOLDER = "assistant_outputs"


def save_binary_response_content(binary_content):
    # Function to get the current timestamp
    def get_timestamp():
        return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # Function to determine the file extension based on the magic numbers (file signatures)
    def get_file_extension(byte_string):
        if byte_string.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"
        elif byte_string.startswith(b"\xff\xd8\xff\xe0") or byte_string.startswith(
            b"\xff\xd8\xff\xe1"
        ):
            return "jpg"
        elif byte_string.startswith(b"GIF87a") or byte_string.startswith(b"GIF89a"):
            return "gif"
        elif byte_string.startswith(b"%PDF-"):
            return "pdf"
        # Add more signatures as needed
        else:
            return "bin"  # Generic binary file extension

    # Get the file extension
    extension = get_file_extension(binary_content)

    # Create a unique file name using the timestamp
    timestamp = get_timestamp()
    file_name = f"file_{timestamp}.{extension}"
    file_path = os.path.join(OUTPUT_FOLDER, file_name)

    # Save the content to the file
    with open(file_path, "wb") as file:
        file.write(binary_content)
        print(f"File saved as {file_path}")

    return file_path


class EventHandler(AssistantEventHandler):
    def __init__(self, output_queue) -> None:
        super().__init__()
        self._images = []
        self.action_manager = ActionsManager()  # singleton
        self.output_queue = output_queue

    @property
    def images(self):
        return self._images

    @override
    def on_text_created(self, text) -> None:
        print("assistant > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        if delta.annotations:
            print(delta.annotations, end="", flush=True)

    def on_image_file_done(self, image_file) -> None:
        content = client.files.content(image_file.file_id)
        image_file = save_binary_response_content(content.content)
        print(f"File saved as {image_file}")
        self._images += [image_file]

    def on_tool_call_created(self, tool_call):
        if tool_call.type == "code_interpreter":
            print("# >>> Code Interpreter", flush=True)

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print("\nOutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"{output.logs}", flush=True)

    @override
    def on_event(self, event):
        # Retrieve events that are denoted with 'requires_action'
        # since these will have our tool_calls
        if event.event == "thread.run.requires_action":
            run_id = event.data.id  # Retrieve the run ID from the event data
            self.handle_requires_action(event.data, run_id)

    def handle_requires_action(self, data, run_id):
        tool_outputs = []

        for tool in data.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name in self.action_manager.get_action_names():
                action = self.action_manager.get_action(tool.function.name)
                if action:
                    args = json.loads(tool.function.arguments)
                    output = action["pointer"](**args)

                    if hasattr(output, "data"):
                        for el in output.data:
                            if hasattr(el, "content"):
                                for c in el.content:
                                    if hasattr(c, "image_file"):
                                        self.on_image_file_done(c.image_file)

                    tool_outputs.append(
                        {"tool_call_id": tool.id, "output": str(output)}
                    )
                    print(
                        f"action: {tool.function.name}(args={tool.function.arguments}) -> {str(output)}"
                    )

        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)

    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=tool_outputs,
            event_handler=EventHandler(self.output_queue),
        ) as stream:
            for text in stream.text_deltas:
                self.output_queue.put(("text", text))
