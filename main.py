import queue
import re
import threading
from contextlib import contextmanager
import os

import gradio as gr

from playground.actions_manager import ActionsManager
from playground.assistants_api import api
from playground.assistants_panel import assistants_panel
from playground.assistants_utils import EventHandler, get_tools
from playground.btree_runner_panel import btree_runner_panel
from playground.environment_manager import EnvironmentManager
from playground.logging import Logger
from playground.semantic_manager import SemanticManager
from playground.global_values import GlobalValues
import argparse

# thread = api.create_thread()  # create a new thread everytime this is run
actions_manager = ActionsManager()
semantic_manager = SemanticManager()

# create code environment
env_manager = EnvironmentManager()
env_manager.install_requirements()

logger = Logger("logs.txt")
logger.reset_logs()

current_thread = None


def create_new_thread():
    global current_thread
    current_thread = api.create_thread()
    return "New thread created."


create_new_thread()


def print_like_dislike(x: gr.LikeData):
    print(x.index, x.value, x.liked)


def ask_assistant(assistant_id, history, message):
    assistant = api.retrieve_assistant(assistant_id)
    if assistant is None:
        history.append((None, "Assistant not found."))
        return history, gr.MultimodalTextbox(value=None, interactive=False)

    if history is None:
        history = []

    attachments = []
    content = ""
    for file in message["files"]:
        tools, actions = get_tools(assistant.tools)
        if "Code Interpreter" in tools:
            # upload files to the thread
            file = api.upload_file(file)
            attachments += [
                {"file_id": file.id, "tools": [{"type": "code_interpreter"}]}
            ]
        else:
            with open(file, "r") as f:
                file_content = f.read()
            file = os.path.basename(file)
            file_path = os.path.join(GlobalValues.ASSISTANTS_WORKING_FOLDER, file)
            with open(file_path, "w") as file:
                file.write(file_content)
                attachments = None
            history.append((f"file {file}, saved to working folder.", None))

    if message["text"] is not None:
        history.append((message["text"], None))
        content = message["text"]
    if content or attachments:  # only create a message if there is content
        api.create_thread_message(
            current_thread.id, "user", content, attachments=attachments
        )

    return history, gr.MultimodalTextbox(value=None, interactive=False)


@contextmanager
def dummy_stream(*args, **kwargs):
    yield ["streaming data"]


def extract_file_paths(text):
    # Regular expression pattern to match file paths
    # This pattern matches typical file paths in Windows and Unix-like systems
    pattern = r"(?:[a-zA-Z]:\\)?(?:[a-zA-Z0-9_-]+\\)*[a-zA-Z0-9_-]+\.[a-zA-Z0-9]+|(?:\/[a-zA-Z0-9_-]+)+\/?"

    # Find all matching file paths in the text
    file_paths = re.findall(pattern, text)

    unique_file_paths = list(set(file_paths))

    return unique_file_paths


def get_file_path(file):
    if os.path.isabs(file):
        return file

    file_path = os.path.join(GlobalValues.ASSISTANTS_WORKING_FOLDER, file)
    return file_path


def run(history, assistant_id, artifacts):
    if current_thread is None:
        history.append((None, "Please create a new thread first."))
        yield (
            history,
            artifacts,
            gr.update(visible=artifacts),
        )
        return

    assistant = api.retrieve_assistant(assistant_id)
    output_queue = queue.Queue()
    eh = EventHandler(output_queue)

    if assistant is None:
        msg = "Assistant not found."
        history.append((None, msg))
        yield (
            history,
            artifacts,
            gr.update(visible=artifacts),
        )
        return

    def stream_worker(assistant_id, thread_id, event_handler):
        with api.run_stream(
            thread_id=thread_id,
            assistant_id=assistant_id,
            event_handler=event_handler,
        ) as stream:
            for text in stream.text_deltas:
                output_queue.put(("text", text))

    # Start the initial stream
    thread_id = current_thread.id
    initial_thread = threading.Thread(
        target=stream_worker, args=(assistant.id, thread_id, eh)
    )
    initial_thread.start()
    history[-1][1] = ""
    while initial_thread.is_alive() or not output_queue.empty():
        try:
            item_type, item_value = output_queue.get(timeout=0.1)
            if item_type == "text":
                history[-1][1] += item_value
            yield history

        except queue.Empty:
            pass
    # history[-1][1] = wrap_latex_with_markdown(history[-1][1])
    yield history

    files = extract_file_paths(history[-1][1])
    for file in files:
        file_path = get_file_path(file)
        if os.path.exists(file_path):
            history.append((None, (file_path,)))
        yield history

    # Final flush of images
    while len(eh.images) > 0:
        history.append((None, (eh.images.pop(),)))
        yield history

    initial_thread.join()
    return None


def main_interface():
    parser = argparse.ArgumentParser(description="GPT Assistants Playground")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the app on")
    parser.add_argument("--share", action="store_true", help="Create a public link")
    parser.add_argument(
        "--in-browser", action="store_true", help="Open in browser", default=True
    )
    parser.add_argument("--show-error", action="store_true", help="Show error messages")
    parser.add_argument("--debug", action="store_true", help="Debug mode")

    args = parser.parse_args()

    # Custom CSS
    custom_css = """
    :root {
        --adjustment-ratio: 150px; /* Height to subtract from the viewport for chatbot */
        --iframe-ratio: 150px; /* Height of the iframe */
    }

    body, html {
        height: 100%;
        width: 100%;
        margin: 0;
        padding: 0;
    }

    .gradio-container {
        max-width: 100% !important; 
        width: 100%;
    }

    #chatbot {
        height: calc(100vh - var(--adjustment-ratio)) !important; /* Uses adjustment ratio */
        overflow-y: auto !important;
    }

    #instructions textarea {
        min-height: calc(100vh - (var(--adjustment-ratio) + 575px)); /* Additional subtraction to account for other elements */
        max-height: 1000px;
        resize: vertical;
        overflow-y: auto;
    }
    #assistant_logs textarea {
        height: calc(100vh - (var(--adjustment-ratio) - 25px)); /* Initial height calculation */
        min-height: 150px; /* Set a reasonable min-height */
        max-height: 1000px; /* Max height of 1000px */
        resize: vertical; /* Allow vertical resizing only */
        overflow-y: auto; /* Enable vertical scrollbar when content exceeds max-height */
        box-sizing: border-box; /* Ensure padding and border are included in the height calculation */
    }

    #actionsnew { 
        color: #000000; 
    }

    #actions { 
        color: #000000; 
    }
    
    video {
        width: 300px;  /* initial width */
        height: 200px; /* initial height */
        transition: width 0.5s ease, height 0.5s ease;
        cursor: pointer;
    }
    video:hover {
        width: auto;
        height: auto;
        max-width: 100%; /* ensures it doesn’t exceed the container's width */
    }
    
    #prefect {
        height: calc(100vh - var(--iframe-ratio)) !important; /* Uses adjustment ratio */
        overflow-y: auto !important;
    }
    """

    prefect_url = "http://127.0.0.1:4200/dashboard"

    iframe_html = f'<iframe id="prefect" src="{prefect_url}" width="100%" height="600px"></iframe>'

    # theme = gr.themes.Default()

    # theme = gr.themes.Glass()
    # theme = gr.themes.Monochrome()
    # theme = gr.themes.Soft()
    theme = "gstaff/sketch"

    with gr.Blocks(
        css=custom_css, theme=theme, title="GPT Assistants Playground"
    ) as demo:
        with gr.Tab(label="Playground"):
            with gr.Row():
                with gr.Column(scale=4):
                    assistant_id = assistants_panel(actions_manager)

                with gr.Column(scale=8):
                    chatbot = gr.Chatbot(
                        [],
                        elem_id="chatbot",
                        bubble_full_width=True,
                        container=True,
                        avatar_images=["avatar1.png", "avatar2_lite.png"],
                        layout="panel",
                    )
                    with gr.Row():
                        with gr.Column(scale=12):
                            chat_input = gr.MultimodalTextbox(
                                interactive=True,
                                file_types=["image"],
                                placeholder="Enter message or upload file...",
                                show_label=False,
                                elem_id="chat_input",
                            )
                        with gr.Column(scale=1):
                            new_thread_button = gr.Button(
                                "Create New Thread", size="lg"
                            )

                new_thread_button.click(create_new_thread, [], None)

                chat_msg = chat_input.submit(
                    ask_assistant,
                    [assistant_id, chatbot, chat_input],
                    [chatbot, chat_input],
                )
                bot_msg = chat_msg.then(
                    run,
                    [chatbot, assistant_id],
                    [chatbot],
                    api_name="assistant_response",
                )
                bot_msg.then(
                    lambda: gr.MultimodalTextbox(interactive=True),
                    None,
                    [chat_input],
                )

                chatbot.like(print_like_dislike, None, None)

        with gr.Tab(label="Agentic Behavior Tree Runner"):
            with gr.Column(scale=4):
                btree_runner = btree_runner_panel()

        with gr.Tab(label="Prefect Flow Runner"):
            gr.HTML(iframe_html)

        with gr.Tab(label="Logs"):
            with gr.Column(scale=4):
                # Add logs
                logs = gr.Code(
                    label="",
                    language="python",
                    interactive=False,
                    container=True,
                    lines=45,
                )
                demo.load(logger.read_logs, None, logs, every=1)
    demo.queue()
    # demo.launch(share=True, inbrowser=True)
    demo.launch(
        share=args.share,
        inbrowser=args.in_browser,
        show_error=args.show_error,
        debug=args.debug,
    )


if __name__ == "__main__":
    main_interface()
    # use the following to launch in browser with a shareable link
