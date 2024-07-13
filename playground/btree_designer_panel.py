import json

import gradio as gr


def get_html_tree(tree):
    base_html_tree = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Behavior Tree</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                }}

                .tree ul {{
                    padding-top: 20px;
                    position: relative;
                    transition: all 0.5s;
                }}

                .tree li {{
                    float: left;
                    text-align: center;
                    list-style-type: none;
                    position: relative;
                    padding: 20px 5px 0 5px;
                    transition: all 0.5s;
                }}

                .tree li::before, .tree li::after {{
                    content: '';
                    position: absolute;
                    top: 0;
                    right: 50%;
                    border-top: 1px solid #ccc;
                    width: 50%;
                    height: 20px;
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
                    height: 20px;
                }}

                .tree li span.node {{
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 25px;
                    height: 25px;
                    padding: 5px;
                    border-radius: 5px;
                    color: black;
                    font-weight: bold;
                    text-decoration: none;
                    position: relative;
                    border: 1px solid black;
                    box-sizing: border-box;
                }}

                .tree li span.node.selector {{
                    background: white;
                }}

                .tree li span.node.sequence {{
                    background: white;
                }}

                .tree li span.node.parallel {{
                    background: white;
                }}

                .tree li span.node.condition {{
                    background: yellow;
                    border-radius: 50px;
                    width: auto;
                    height: auto;
                }}

                .tree li span.node.action {{
                    background: green;
                    border-radius: 5px;
                    color: white;
                    width: auto;
                    height: auto;
                }}

                .tree li span.node.decorator {{
                    background: white;
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
    if node["children"]:
        html += "<ul>"
        for child in node["children"]:
            html += "<li>" + convert_to_html(child) + "</li>"
        html += "</ul>"

    return html


def json_to_html_tree(json_tree):
    tree = json.loads(json_tree)
    html = '<div class="tree"><ul><li>'
    html += convert_to_html(tree)
    html += "</li></ul></div>"
    return get_html_tree(html)


class BehaviorTreeNode:
    def __init__(self, name, node_type):
        self.name = name
        self.type = node_type
        self.children = []
        self.prompt = ""  # New property to hold function/condition

    def to_dict(self):
        dict = {
            "name": self.name,
            "type": self.type,
            "children": [child.to_dict() for child in self.children],
        }
        if self.prompt:
            dict["prompt"] = self.prompt
        return dict

    @staticmethod
    def from_dict(node_dict):
        name = node_dict["name"]
        node_type = node_dict["type"]
        prompt = node_dict.get("prompt", "")
        if node_type == "Selector":
            node = Selector(name)
        elif node_type == "Sequence":
            node = Sequence(name)
        elif node_type == "Condition":
            node = Condition(name)
        elif node_type == "Action":
            node = Action(name)
        elif node_type == "Decorator":
            node = Decorator(name)
        elif node_type == "Parallel":
            node = Parallel(name)
        else:
            node = BehaviorTreeNode(name, node_type)
        node.prompt = prompt
        node.children = [
            BehaviorTreeNode.from_dict(child) for child in node_dict["children"]
        ]
        return node


class Selector(BehaviorTreeNode):
    def __init__(self, name="Selector"):
        super().__init__(name, "Selector")


class Sequence(BehaviorTreeNode):
    def __init__(self, name="Sequence"):
        super().__init__(name, "Sequence")


class Condition(BehaviorTreeNode):
    def __init__(self, name):
        super().__init__(name, "Condition")


class Action(BehaviorTreeNode):
    def __init__(self, name):
        super().__init__(name, "Action")


class Decorator(BehaviorTreeNode):
    def __init__(self, name="Decorator"):
        super().__init__(name, "Decorator")


class Parallel(BehaviorTreeNode):
    def __init__(self, name="Parallel"):
        super().__init__(name, "Parallel")


root_node = None


def add_node(node_type, name):
    global root_node

    # Create the new node
    if node_type == "Selector":
        new_node = Selector(name)
    elif node_type == "Sequence":
        new_node = Sequence(name)
    elif node_type == "Condition":
        new_node = Condition(name)
    elif node_type == "Action":
        new_node = Action(name)
    elif node_type == "Decorator":
        new_node = Decorator(name)
    elif node_type == "Parallel":
        new_node = Parallel(name)
    else:
        return "Invalid node type", None, []

    if root_node is None:
        root_node = new_node
    else:
        return "Root node already exists", None, []

    node_list = get_node_names(root_node)
    json_tree = json.dumps(root_node.to_dict(), indent=2)
    return (
        json_tree,
        json_to_html_tree(json_tree),
        gr.update(choices=node_list, visible=True),
    )


def get_node_names(node):
    names = [node.name]
    for child in node.children:
        names.extend(get_node_names(child))
    return names


def create_node_panel(node_selection):
    if node_selection == "Create New Node":
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
        )
    node = find_node(root_node, node_selection)
    if node is not None and node.type in [
        "Selector",
        "Sequence",
        "Decorator",
        "Parallel",
    ]:
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
        )
    elif node is not None and node.type in ["Action", "Condition"]:
        return (
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
        )
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def add_child_node(parent_name, child_type, child_name):
    global root_node
    parent_node = find_node(root_node, parent_name)
    if not parent_node:
        return f"Parent node '{parent_name}' not found", None, []

    if child_type == "Selector":
        new_child = Selector(child_name)
    elif child_type == "Sequence":
        new_child = Sequence(child_name)
    elif child_type == "Condition":
        new_child = Condition(child_name)
    elif child_type == "Action":
        new_child = Action(child_name)
    elif child_type == "Decorator":
        new_child = Decorator(child_name)
    elif child_type == "Parallel":
        new_child = Parallel(child_name)
    else:
        return "Invalid child node type", None, []

    parent_node.children.append(new_child)
    node_list = get_node_names(root_node)
    json_tree = json.dumps(root_node.to_dict(), indent=2)
    return json_tree, json_to_html_tree(json_tree), gr.update(choices=node_list)


def set_node_prompt(node_name, prompt):
    global root_node
    target_node = find_node(root_node, node_name)
    if not target_node:
        return f"Node '{node_name}' not found", None, []

    target_node.prompt = prompt
    json_tree = json.dumps(root_node.to_dict(), indent=2)
    return (
        json_tree,
        json_to_html_tree(json_tree),
        gr.update(choices=get_node_names(root_node)),
    )


def find_node(node, name):
    if node is None:
        return None
    if node.name == name:
        return node
    for child in node.children:
        found = find_node(child, name)
        if found:
            return found
    return None


def update_child_or_function_controls(node_name):
    target_node = find_node(root_node, node_name)
    if target_node:
        if target_node.type in ["Selector", "Sequence", "Decorator", "Parallel"]:
            return gr.update(visible=True), gr.update(visible=False)
        elif target_node.type in ["Action", "Condition"]:
            return gr.update(visible=False), gr.update(visible=True)
    return gr.update(visible=False), gr.update(visible=False)


def behavior_panel():
    node_names = gr.State(value=[])

    with gr.Row():
        with gr.Column():
            select_node_dropdown = gr.Dropdown(
                label="Select Node", choices=["Create New Node"], interactive=True
            )
            node_creation_panel = gr.Group(visible=False)

            with node_creation_panel:
                node_name_input = gr.Textbox(label="Node Name")
                node_type_dropdown = gr.Dropdown(
                    choices=[
                        "Selector",
                        "Sequence",
                        "Condition",
                        "Action",
                        "Decorator",
                        "Parallel",
                    ],
                    label="Node Type",
                )
                create_button = gr.Button("Create Node")

            with gr.Group(visible=False) as child_node_panel:
                child_name_input = gr.Textbox(label="Child Node Name")
                child_type_dropdown = gr.Dropdown(
                    choices=[
                        "Selector",
                        "Sequence",
                        "Condition",
                        "Action",
                        "Decorator",
                        "Parallel",
                    ],
                    label="Child Node Type",
                )
                add_child_button = gr.Button("Add Child Node")

            with gr.Group(visible=False) as prompt_node_panel:
                prompt_text = gr.Textbox(label="Action/Condition Prompt", lines=3)
                set_function_button = gr.Button("Set Action/Condition Prompt")

            btree_display = gr.HTML(label="Rendered HTML")

        with gr.Column():
            tree_json_label = gr.Markdown("### Tree JSON")
            tree_json_display = gr.Code(
                label="", language="json", interactive=False, container=True, lines=30
            )

    select_node_dropdown.change(
        create_node_panel,
        inputs=[select_node_dropdown],
        outputs=[node_creation_panel, child_node_panel, prompt_node_panel],
    )
    create_button.click(
        add_node,
        inputs=[node_type_dropdown, node_name_input],
        outputs=[tree_json_display, btree_display, select_node_dropdown],
    )
    select_node_dropdown.change(
        update_child_or_function_controls,
        inputs=[select_node_dropdown],
        outputs=[child_node_panel, prompt_node_panel],
    )
    add_child_button.click(
        add_child_node,
        inputs=[select_node_dropdown, child_type_dropdown, child_name_input],
        outputs=[tree_json_display, btree_display, select_node_dropdown],
    )
    set_function_button.click(
        set_node_prompt,
        inputs=[select_node_dropdown, prompt_text],
        outputs=[tree_json_display, btree_display, select_node_dropdown],
    )


# demo.launch()
