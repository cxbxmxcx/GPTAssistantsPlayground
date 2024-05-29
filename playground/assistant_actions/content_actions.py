from playground.actions_manager import agent_action


@agent_action
def get_content_length_characters(content):
    """Returns the length of the content in characters."""
    return len(content)
