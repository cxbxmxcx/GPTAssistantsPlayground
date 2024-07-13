import time

import gradio as gr

from playground.assistants_api import api
from playground.assistants_utils import (
    get_actions_by_name,
    get_tools,
    get_tools_by_name,
)


def assistants_panel(actions_manager):
    available_actions = actions_manager.get_actions()

    def list_assistants():
        assistant_choices = api.list_assistants()
        assistant_options = {a.name: a.id for a in assistant_choices.data}
        assistant_options["Create New Assistant"] = "new"
        return assistant_options

    assistant_options = list_assistants()

    def update_assistant(
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
        if assistant_id is not None and len(assistant_id) > 5:
            tools = get_tools_by_name(assistant_tools)
            actions = get_actions_by_name(assistant_actions, available_actions)
            api.update_assistant(
                assistant_name,
                assistant_id,
                assistant_instructions,
                assistant_model,
                tools,
                actions,
                assistant_resformat,
                assistant_temperature,
                assistant_top_p,
            )

    def create_assistant(
        assistant_name_new,
        assistant_instructions_new,
        assistant_model_new,
        assistant_tools_new,
        assistant_actions_new,
        assistant_resformat_new,
        assistant_temperature_new,
        assistant_top_p_new,
    ):
        tools = [
            {"type": "file_search"}
            if tool == "File search"
            else {"type": "code_interpreter"}
            for tool in assistant_tools_new
        ]
        actions = [
            action["agent_action"]
            for action in available_actions
            if action["name"] in assistant_actions_new
        ]
        format = "auto"  # "type" if assistant_resformat_new == "JSON object" else "auto"  TODO: fix this
        new_assistant = api.create_assistant(
            assistant_name_new,
            assistant_instructions_new,
            assistant_model_new,
            tools,
            actions,
            format,
            assistant_temperature_new,
            assistant_top_p_new,
        )
        return new_assistant.id

    def get_assistant_details(assistant_key):
        assistant_options = list_assistants()
        if assistant_key == "Create New Assistant":
            return "", "", "", "gpt-4o", [], "", "", 1, 1
        else:
            if assistant_key in assistant_options.keys():
                assistant_id = assistant_options[assistant_key]
            else:
                assistant_id = assistant_key

            assistant = api.retrieve_assistant(assistant_id)
            actions = []
            if assistant.tools is None:
                tools = []
            else:
                tools, actions = get_tools(assistant.tools)
            format = "type" if assistant.response_format == "JSON object" else "auto"

            return (
                assistant.name,
                assistant.id,
                assistant.instructions,
                assistant.model,
                tools,
                actions,
                format,
                assistant.temperature,
                assistant.top_p,
            )

    def assistant_selected_change(assistant_key):
        if assistant_key == "Create New Assistant":
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
            )
        else:
            return (
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=True),
            )

    action_choices = sorted([action["name"] for action in available_actions])
    assistant_selected = gr.Dropdown(
        label="Select Assistant",
        choices=assistant_options.keys(),
        interactive=True,
    )

    with gr.Column(visible=False) as new_assistant_form:
        assistant_name_new = gr.Textbox(
            label="Enter a user-friendly name",
            placeholder="Enter Name",
            interactive=True,
        )
        assistant_instructions_new = gr.Textbox(
            label="Instructions",
            placeholder="You are a helpful assistant.",
            elem_id="instructions",
            interactive=True,
        )
        assistant_model_new = gr.Dropdown(
            label="Model",
            choices=["gpt-3", "gpt-3.5", "gpt-4", "gpt-4o"],
            value="gpt-4o",
            interactive=True,
        )
        assistant_tools_new = gr.CheckboxGroup(
            label="Tools", choices=["File search", "Code interpreter"], interactive=True
        )
        # assistant_files_new = gr.Textbox(
        #     label="Add Files or Functions", placeholder="+ Files, + Functions"
        # )
        with gr.Accordion("Actions", open=False, elem_id="actionsnew"):
            assistant_actions_new = gr.CheckboxGroup(
                label="Actions", choices=action_choices, interactive=True
            )
        with gr.Accordion("Model settings", open=False, elem_id="modelsettingsnew"):
            assistant_resformat_new = gr.Radio(
                label="Response Format",
                choices=["JSON object", "Plain text"],
                value="JSON object",
                interactive=True,
            )
            assistant_temperature_new = gr.Slider(
                label="Temperature",
                minimum=0,
                maximum=1,
                step=0.01,
                value=1,
                interactive=True,
            )
            assistant_top_p_new = gr.Slider(
                label="Top P",
                minimum=0,
                maximum=1,
                step=0.01,
                value=1,
                interactive=True,
            )
        add_button = gr.Button("Add Assistant", interactive=True, visible=True)

    with gr.Column(visible=True) as existing_assistant_form:
        assistant_id = gr.Markdown("ID:")
        assistant_name = gr.Textbox(
            label="Enter a user-friendly name", placeholder="Enter Name"
        )
        assistant_instructions = gr.Textbox(
            label="Instructions",
            placeholder="You are a helpful assistant.",
            elem_id="instructions",
        )
        assistant_model = gr.Dropdown(
            label="Model",
            choices=["gpt-3", "gpt-3.5", "gpt-4", "gpt-4o"],
            value="gpt-4o",
        )
        assistant_tools = gr.CheckboxGroup(
            label="Tools", choices=["File search", "Code interpreter"]
        )
        with gr.Accordion("Actions", open=False, elem_id="actions"):
            assistant_actions = gr.CheckboxGroup(
                label="Actions", choices=action_choices, interactive=True
            )
        with gr.Accordion("Model settings", open=False, elem_id="modelsettings"):
            assistant_resformat = gr.Radio(
                label="Response Format",
                choices=["JSON object", "Plain text"],
                value="JSON object",
            )
            assistant_temperature = gr.Slider(
                label="Temperature", minimum=0, maximum=1, step=0.01, value=1
            )
            assistant_top_p = gr.Slider(
                label="Top P", minimum=0, maximum=1, step=0.01, value=1
            )
        delete_button = gr.Button("🗑️")

    assistant_selected.change(
        fn=get_assistant_details,
        inputs=assistant_selected,
        outputs=[
            assistant_name,
            assistant_id,
            assistant_instructions,
            assistant_model,
            assistant_tools,
            assistant_actions,
            assistant_resformat,
            assistant_temperature,
            assistant_top_p,
        ],
    )

    assistant_selected.change(
        fn=assistant_selected_change,
        inputs=assistant_selected,
        outputs=[
            new_assistant_form,
            existing_assistant_form,
            add_button,
            delete_button,
        ],
    )

    controls = [
        assistant_name,
        assistant_id,
        assistant_instructions,
        assistant_model,
        assistant_tools,
        assistant_actions,
        assistant_resformat,
        assistant_temperature,
        assistant_top_p,
    ]

    for control in controls:
        control.change(fn=update_assistant, inputs=controls, outputs=[])

    def create_and_select_assistant(
        assistant_name_new,
        assistant_instructions_new,
        assistant_model_new,
        assistant_tools_new,
        assistant_actions_new,
        assistant_resformat_new,
        assistant_temperature_new,
        assistant_top_p_new,
    ):
        new_assistant_id = create_assistant(
            assistant_name_new,
            assistant_instructions_new,
            assistant_model_new,
            assistant_tools_new,
            assistant_actions_new,
            assistant_resformat_new,
            assistant_temperature_new,
            assistant_top_p_new,
        )
        time.sleep(2)  # wait for assistant to be created
        assistant_options = list_assistants()
        return (
            gr.update(choices=list(assistant_options.keys()), value=new_assistant_id),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=True),
        )

    def delete_and_select_assistant(assistant_id):
        api.delete_assistant(assistant_id)
        assistant_options = list_assistants()
        return (
            gr.update(
                choices=list(assistant_options.keys()), value="Create New Assistant"
            ),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
        )

    add_button.click(
        fn=create_and_select_assistant,
        inputs=[
            assistant_name_new,
            assistant_instructions_new,
            assistant_model_new,
            assistant_tools_new,
            assistant_actions_new,
            assistant_resformat_new,
            assistant_temperature_new,
            assistant_top_p_new,
        ],
        outputs=[
            assistant_selected,
            new_assistant_form,
            existing_assistant_form,
            add_button,
            delete_button,
        ],
    )

    delete_button.click(
        fn=delete_and_select_assistant,
        inputs=[assistant_id],
        outputs=[
            assistant_selected,
            new_assistant_form,
            existing_assistant_form,
            add_button,
            delete_button,
        ],
    )

    return assistant_id
