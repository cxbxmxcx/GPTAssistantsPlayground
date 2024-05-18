import queue
import threading
from contextlib import contextmanager

import gradio as gr

from playground.actions_manager import ActionsManager
from playground.assistants_api import api
from playground.assistants_panel import assistants_panel
from playground.assistants_utils import EventHandler
from playground.semantic_manager import SemanticManager

thread = api.create_thread()  # create a new thread everytime this is run
actions_manager = ActionsManager()
semantic_manager = SemanticManager()
# Chatbot demo with multimodal input (text, markdown, LaTeX, code blocks, image, audio, & video). Plus shows support for streaming text.


def wrap_latex_with_markdown(text):
    system = """You are a LaTeX genius and equation genius!,
    Your job is to identify LaTeX and equations in the text. 
    For each block of LaTeX or equation text you will wrap it with $ if the block is inline,
    or with $$ if the block is on its own line.
    """
    user = text
    text = semantic_manager.get_semantic_response(system, user)
    return text
    # # Regular expression to find LaTeX enclosed in [] or ()
    # bracket_pattern = re.compile(r"\[(.*?)\]")
    # parenthesis_pattern = re.compile(r"\((.*?)\)")

    # # Replace LaTeX within brackets with Markdown inline math
    # text = bracket_pattern.sub(r"$$\1$$", text)

    # # Replace LaTeX within parentheses with Markdown inline math
    # text = parenthesis_pattern.sub(r"$$\1$$", text)
    # return text


def print_like_dislike(x: gr.LikeData):
    print(x.index, x.value, x.liked)


def ask_assistant(history, message):
    if history is None:
        history = []

    attachments = []
    content = ""
    for file in message["files"]:
        history.append(((file,), None))
        # upload files to the thread
        file = api.upload_file(file)
        attachments += [{"file_id": file.id, "tools": [{"type": "code_interpreter"}]}]
    if message["text"] is not None:
        history.append((message["text"], None))
        content = message["text"]
    if content or attachments:  # only create a message if there is content
        api.create_thread_message(thread.id, "user", content, attachments=attachments)

    return history, gr.MultimodalTextbox(value=None, interactive=False)


@contextmanager
def dummy_stream(*args, **kwargs):
    yield ["streaming data"]


def run(history, assistant_id, logs):
    assistant = api.retrieve_assistant(assistant_id)
    output_queue = queue.Queue()
    eh = EventHandler([logs], actions_manager, output_queue)

    if assistant is None:
        msg = "Assistant not found."
        history.append((None, msg))
        yield history, msg
        return

    def stream_worker(assistant_id, thread_id, event_handler):
        with api.run_stream(
            thread_id=thread_id, assistant_id=assistant_id, event_handler=event_handler
        ) as stream:
            for text in stream.text_deltas:
                output_queue.put(("text", text))

    # Start the initial stream
    thread_id = thread.id
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
                # history[-1][1] = wrap_latex_with_markdown(history[-1][1])
            yield history, "".join(eh.logs)

        except queue.Empty:
            pass
    history[-1][1] = wrap_latex_with_markdown(history[-1][1])
    yield history, "".join(eh.logs)
    # Final flush of images
    while len(eh.images) > 0:
        history.append((None, (eh.images.pop(),)))
        yield history, "".join(eh.logs)

    initial_thread.join()
    return None, "".join(eh.logs)


# Custom CSS
custom_css = """
:root {
    --adjustment-ratio: 150px; /* Height to subtract from the viewport for chatbot */
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
    min-height: calc(100vh - (var(--adjustment-ratio) + 750px)); /* Additional subtraction to account for other elements */
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
"""

with gr.Blocks(css=custom_css) as demo:
    # assistant_logs = gr.TextArea(label="Assistant Logs", placeholder="Logs here...", elem_id="assistant_logs", interactive=False, render=False)
    assistant_logs = gr.Markdown(
        "Assistant Logs", elem_id="assistant_logs", render=False
    )
    with gr.Row():
        with gr.Column(scale=4):
            assistant_id = assistants_panel(actions_manager)

        with gr.Column(scale=8):
            chatbot = gr.Chatbot(
                [],
                elem_id="chatbot",
                bubble_full_width=True,
                container=True,
                avatar_images=["avatar1.png", "avatar2.png"],
                layout="panel",
            )

            chat_input = gr.MultimodalTextbox(
                interactive=True,
                file_types=["image"],
                placeholder="Enter message or upload file...",
                show_label=False,
                elem_id="chat_input",
            )

            chat_msg = chat_input.submit(
                ask_assistant, [chatbot, chat_input], [chatbot, chat_input]
            )
            bot_msg = chat_msg.then(
                run,
                [chatbot, assistant_id, assistant_logs],
                [chatbot, assistant_logs],
                api_name="assistant_response",
            )
            bot_msg.then(
                lambda: gr.MultimodalTextbox(interactive=True), None, [chat_input]
            )

            chatbot.like(print_like_dislike, None, None)
        with gr.Column(scale=2):
            assistant_logs.render()

demo.queue()


if __name__ == "__main__":
    demo.launch()
