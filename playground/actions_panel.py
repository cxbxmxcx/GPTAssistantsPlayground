import gradio as gr


def assistants_actions_panel(actions_manager):
    available_actions = actions_manager.get_actions()

    # Group actions by their group property
    action_groups = {}
    for action in available_actions:
        group = action.get("group", "Ungrouped")
        if group not in action_groups:
            action_groups[group] = []
        action_groups[group].append(action["name"])

    with gr.Accordion("Actions", open=False):
        group_accordions = []
        for group, actions in action_groups.items():
            with gr.Accordion(group, open=False) as group_accordion:
                group_checkbox = gr.CheckboxGroup(
                    label=f"{group} Actions", choices=actions, interactive=True
                )
                group_accordions.append((group_accordion, group_checkbox))

        # Hidden control to store all selected actions
        assistant_actions = gr.CheckboxGroup(
            label="All Selected Actions", choices=[], visible=False
        )

    def sync_actions(selected_actions):
        # Update the assistant actions control with the new selection
        assistant_actions.update(value=selected_actions)
        return selected_actions

    # Create a change listener for each group's checkbox group
    for _, group_checkbox in group_accordions:
        group_checkbox.change(
            fn=sync_actions, inputs=group_checkbox, outputs=assistant_actions
        )

    return assistant_actions


# Example usage
if __name__ == "__main__":

    class ActionsManager:
        def get_actions(self):
            return [
                {"name": "Action1", "group": "Group1"},
                {"name": "Action2", "group": "Group1"},
                {"name": "Action3", "group": "Group2"},
                {"name": "Action4", "group": "Group2"},
                {"name": "Action5", "group": "Group3"},
            ]

    actions_manager = ActionsManager()
    demo = gr.Interface(
        fn=lambda x: x, inputs=assistants_actions_panel(actions_manager), outputs="text"
    )
    demo.launch()
