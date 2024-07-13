import os
import threading
import time
import yaml
import gradio as gr
from playground.behavior_tree_manager import BehaviorTreeManager


def get_html_tree(tree):
    base_html_tree = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Behavior Tree</title>
            <style>
                :root {{
                    --node-size: calc(2vw);
                    --padding-size: calc(1% + 10px);
                    --font-size: calc(0.5% + 12px);
                    --connector-height: calc(1% + 10px);
                }}

                body {{
                    font-family: Arial, sans-serif;
                }}

                .tree ul {{
                    padding-top: var(--padding-size);
                    position: relative;
                    transition: all 0.5s;
                }}

                .tree li {{
                    float: left;
                    text-align: center;
                    list-style-type: none;
                    position: relative;
                    padding: var(--padding-size) 5px 0 5px;
                    transition: all 0.5s;
                }}

                .tree li::before, .tree li::after {{
                    content: '';
                    position: absolute;
                    top: 0;
                    right: 50%;
                    border-top: 1px solid #ccc;
                    width: 50%;
                    height: var(--connector-height);
                }}

                .tree li::after {{
                    right: auto;
                    left: 50%;
                    border-left: 1px solid #ccc;
                }}

                .tree li:only-child::after, .tree li:only-child::before {{
                    display: none;
                }}

                .tree li:only-child {{
                    padding-top: 0;
                }}

                .tree li:first-child::before, .tree li:last-child::after {{
                    border: 0 none;
                }}

                .tree li:last-child::before {{
                    border-right: 1px solid #ccc;
                    border-radius: 0 5px 0 0;
                }}

                .tree li:first-child::after {{
                    border-radius: 5px 0 0 0;
                }}

                .tree ul ul::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 50%;
                    border-left: 1px solid #ccc;
                    width: 0;
                    height: var(--connector-height);
                }}

                .tree li span.node {{
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: var(--node-size);
                    height: var(--node-size);
                    padding: 5px;
                    border-radius: 5px;
                    color: black;
                    font-weight: bold;
                    text-decoration: none;
                    position: relative;
                    border: 1px solid black;
                    box-sizing: border-box;
                    font-size: var(--font-size);
                }}

                .tree li span.node.selector, .tree li span.node.sequence, .tree li span.node.parallel, .tree li span.node.decorator {{
                    background: white;
                }}

                .tree li span.node.condition {{
                    background: yellow;
                    border-radius: 50px;
                }}

                .tree li span.node.action {{
                    background: green;
                    border-radius: 5px;
                    color: white;
                    width: auto;
                    height: auto;
                    padding: 10px;
                }}

                .tree li span.node:hover, .tree li span.node:hover+ul li span.node {{
                    background: #94a8b7;
                    color: white;
                    box-shadow: 0 0 8px 2px #94a8b7;
                }}
            </style>
        </head>
        <body>
            {tree}
        </body>
        </html>
    """
    return base_html_tree


def convert_to_html(node):
    html = ""

    # Determine the type of node and its corresponding HTML class and symbol
    if node["type"] == "Selector":
        html += '<span class="node selector" data-symbol="?">?</span>'
    elif node["type"] == "Sequence":
        html += '<span class="node sequence" data-symbol="→">→</span>'
    elif node["type"] == "Parallel":
        html += '<span class="node parallel" data-symbol="⇉">⇉</span>'
    elif node["type"] == "Decorator":
        html += '<span class="node decorator" data-symbol="◇">◇</span>'
    elif node["type"] == "Action":
        html += f'<span class="node action">{node["name"]}</span>'
    elif node["type"] == "Condition":
        html += f'<span class="node condition">{node["name"]}</span>'

    # If the node has children, process them recursively
    if "children" in node and node["children"]:
        html += "<ul>"
        for child in node["children"]:
            html += "<li>" + convert_to_html(child) + "</li>"
        html += "</ul>"

    return html


def yaml_to_html_tree(yaml_tree):
    tree = yaml.safe_load(yaml_tree)
    root = tree["behavior_tree"]["root"]
    html = '<div class="tree"><ul><li>'
    html += convert_to_html(root)
    html += "</li></ul></div>"
    return get_html_tree(html)


# Global variable to store the current thread running the behavior tree
current_tree_runner = None


class BehaviorTreeRunner(threading.Thread):
    def __init__(self, tree, tick_interval=30):
        super().__init__()
        self.tree = tree
        self.tick_interval = tick_interval
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            self.tree.tick()
            time.sleep(self.tick_interval)

    def stop(self):
        self._stop_event.set()


def run_selected_behavior_tree(yaml_file_path):
    global current_tree_runner
    if current_tree_runner and current_tree_runner.is_alive():
        current_tree_runner.stop()
        current_tree_runner.join()

    manager = BehaviorTreeManager(os.path.dirname(yaml_file_path))
    tree = manager.load_behavior_tree_from_yaml(yaml_file_path)
    current_tree_runner = BehaviorTreeRunner(tree)
    current_tree_runner.start()
    return (
        "Behavior tree is running.",
        gr.update(visible=True),
        gr.update(visible=False),
    )


def display_yaml(yaml_file_path):
    with open(yaml_file_path, "r") as file:
        yaml_content = file.read()
    html_tree = yaml_to_html_tree(yaml_content)
    return yaml_content, html_tree


def update_html_tree(yaml_content):
    html_tree = yaml_to_html_tree(yaml_content)
    return html_tree


def save_yaml(yaml_content, yaml_file_path):
    with open(yaml_file_path, "w") as file:
        file.write(yaml_content)
    return "YAML saved successfully."


def cancel_behavior_tree():
    global current_tree_runner
    if current_tree_runner and current_tree_runner.is_alive():
        current_tree_runner.stop()
        current_tree_runner.join()
        return (
            "Behavior tree execution cancelled.",
            gr.update(visible=False),
            gr.update(visible=True),
        )
    return "No behavior tree is running."


def btree_runner_panel():
    with gr.Blocks() as demo:
        yaml_file = gr.File(
            label="Select Behavior Tree YAML File", file_count="single", type="filepath"
        )
        with gr.Row():
            with gr.Column(scale=6):
                yaml_code_block = gr.Code(
                    label="Behavior Tree YAML Content", language="yaml", lines=20
                )
            with gr.Column(scale=4):
                html_tree = gr.HTML(label="Behavior Tree")

        with gr.Row():
            run_button = gr.Button("Run", visible=True)
            cancel_button = gr.Button("Cancel", visible=False)
            save_button = gr.Button("Save YAML")
        status_box = gr.Textbox(label="Status", interactive=False)

        yaml_file.change(
            display_yaml, inputs=yaml_file, outputs=[yaml_code_block, html_tree]
        )
        yaml_code_block.change(
            update_html_tree, inputs=yaml_code_block, outputs=html_tree
        )
        run_button.click(
            run_selected_behavior_tree,
            inputs=yaml_file,
            outputs=[status_box, cancel_button, run_button],
        )
        cancel_button.click(
            cancel_behavior_tree, outputs=[status_box, cancel_button, run_button]
        )
        save_button.click(
            save_yaml, inputs=[yaml_code_block, yaml_file], outputs=status_box
        )

    return demo


# To use the panel in a larger interface, you can call btree_runner_panel and integrate it as needed.
