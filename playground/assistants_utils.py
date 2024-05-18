import datetime
import json
import textwrap

import openai
from dotenv import load_dotenv
from openai import AssistantEventHandler
from typing_extensions import override

load_dotenv()

# OpenAI client initialization
client = openai.OpenAI()


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

    # Save the content to the file
    with open(file_name, "wb") as file:
        file.write(binary_content)
        print(f"File saved as {file_name}")

    return file_name


class EventHandler(AssistantEventHandler):
    def __init__(self, logs, action_manager, output_queue) -> None:
        super().__init__()
        self._logs = logs
        self._images = []
        self.action_manager = action_manager
        self.output_queue = output_queue

    @property
    def logs(self):
        return self._logs

    @property
    def images(self):
        return self._images

    @override
    def on_text_created(self, text) -> None:
        print("assistant > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        # print(delta.value, flush=True)
        if delta.annotations:
            print(delta.annotations, end="", flush=True)

    @override
    def on_end(self) -> None:
        print("STREAM DONE ", end="", flush=True)

    def on_image_file_done(self, image_file) -> None:
        print(image_file, end="", flush=True)
        content = client.files.content(image_file.file_id)
        image_file = save_binary_response_content(content.content)
        self._logs += [f"File saved as {image_file}"]
        self._images += [image_file]

    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)
        self._logs += [f"\nassistant > {tool_call.type}"]
        if tool_call.type == "code_interpreter":
            self._logs += ["\n```python"]

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
                self._logs += [f"{delta.code_interpreter.input}"]
            if delta.code_interpreter.outputs:
                print("\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"{output.logs}", flush=True)
                        self._logs += [f"{output.logs}"]

        if delta.type == "function":
            if delta.function.arguments:
                print(delta.function.arguments, end="", flush=True)
                self._logs += [f"{delta.function.arguments}"]

    def on_tool_call_done(self, tool_call) -> None:
        if tool_call.type == "code_interpreter":
            self._logs += ["\n```\n"]

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
                    tool_outputs.append(
                        {"tool_call_id": tool.id, "output": str(output)}
                    )
                    self._logs += [
                        textwrap.dedent(f"""
                        <details>
                            <summary>action: {tool.function.name}(args={tool.function.arguments}</summary>
                            <pre>{str(output)}</pre>
                        </details>
                    """)
                    ]

        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)

    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=tool_outputs,
            event_handler=EventHandler(
                self._logs, self.action_manager, self.output_queue
            ),
        ) as stream:
            for text in stream.text_deltas:
                self.output_queue.put(("text", text))
