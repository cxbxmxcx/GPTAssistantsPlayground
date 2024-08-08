import datetime
import json
import os

import openai
from dotenv import load_dotenv
from openai import AssistantEventHandler
from typing_extensions import override

from playground.actions_manager import ActionsManager
from playground.global_values import GlobalValues

load_dotenv()

# OpenAI client initialization
client = openai.OpenAI()


def get_tools(tools):
    tools_list = []
    action_list = []
    for tool in tools:
        if tool.type == "file_search":
            tools_list.append("File search")
        if tool.type == "code_interpreter":
            tools_list.append("Code interpreter")
        if tool.type == "function":
            action_list.append(tool.function.name)
    return tools_list, action_list


def get_tools_by_name(tools):
    tools_list = []
    for tool in tools:
        if tool == "File search":
            tools_list.append({"type": "file_search"})
        if tool == "Code interpreter":
            tools_list.append({"type": "code_interpreter"})
    return tools_list


def get_actions_by_name(actions, available_actions):
    action_list = []
    for action in actions:
        for available_action in available_actions:
            if available_action["name"] == action:
                action_list.append(available_action["agent_action"])
    return action_list


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
    file_path = os.path.join(GlobalValues.ASSISTANTS_WORKING_FOLDER, file_name)

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
        self.internal_context = ""

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

    def on_image_file(self, image_file) -> None:
        self._images += [image_file]

    def on_tool_call_created(self, tool_call):
        if tool_call.type == "code_interpreter":
            print("# >>> Code Interpreter", flush=True)

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
                self.internal_context += delta.code_interpreter.input
            if delta.code_interpreter.outputs:
                print("\nOutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"{output.logs}", flush=True)
                        self.internal_context += output.logs

    @override
    def on_event(self, event):
        # Retrieve events that are denoted with 'requires_action'
        # since these will have our tool_calls
        if event.event == "thread.run.requires_action":
            run_id = event.data.id  # Retrieve the run ID from the event data
            self.handle_requires_action(event.data, run_id)

    def handle_requires_action(
        self,
        data,
        run_id,
    ):
        tool_outputs = []

        for tool in data.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name in self.action_manager.get_action_names():
                action = self.action_manager.get_action(tool.function.name)
                print(f"action: {tool.function.name} -> {action}")
                if action:
                    try:
                        args = json.loads(tool.function.arguments)
                        print(f"action: {tool.function.name} -> {args}")
                        output = action["pointer"](**args)

                        if hasattr(output, "data"):
                            for el in output.data:
                                if hasattr(el, "content"):
                                    for c in el.content:
                                        if hasattr(c, "image_file"):
                                            self.on_image_file_done(c.image_file)
                        elif isinstance(output, str) and ".png" in output:
                            self.on_image_file(output)

                        tool_outputs.append(
                            {"tool_call_id": tool.id, "output": str(output)}
                        )
                        print(
                            f"action: {tool.function.name}(args={tool.function.arguments}) -> {str(output)}"
                        )
                        self.internal_context += str(output)
                    except Exception as e:
                        print(f"Error in action: {tool.function.name} -> {str(e)}")
                        tool_outputs.append({"tool_call_id": tool.id, "output": str(e)})

        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)

    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        try:
            with client.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=self.current_run.thread_id,
                run_id=self.current_run.id,
                tool_outputs=tool_outputs,
                event_handler=EventHandler(self.output_queue),
            ) as stream:
                for text in stream.text_deltas:
                    self.output_queue.put(("text", text))
        except Exception as e:
            msg = f"Run cancelled with error in tool outputs: {str(e)}"
            self.output_queue.put(("text", msg))
            client.beta.threads.runs.cancel(
                run_id=self.current_run.id, thread_id=self.current_run.thread_id
            )
            client.beta.threads.messages.create(
                thread_id=self.current_run.thread_id,
                role="assistant",
                content=msg,
            )
