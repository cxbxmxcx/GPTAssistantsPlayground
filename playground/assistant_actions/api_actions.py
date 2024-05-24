import json

from playground.actions_manager import ActionsManager, agent_action
from playground.assistants_api import api


@agent_action
def list_uploaded_files(purpose="assistants"):
    """Lists all the uploaded files for the given purpose."""
    if purpose not in ["assistants", "playground"]:
        purpose = None
    files = api.list_files(purpose=purpose)
    files = [
        {"id": file.id, "filename": file.filename, "purpose": file.purpose}
        for file in files
    ]
    return json.dumps(files)


@agent_action
def delete_uploaded_file(file_id):
    """Deletes the uploaded file with the given file_id."""
    deleted = api.delete_file(file_id)
    if not deleted:
        return f"Unable to delete file with ID {file_id}."
    return f"File with ID {file_id} deleted successfully."


@agent_action
def list_assistants(self):
    """Lists all the assistants."""
    assistants = api.list_assistants()
    assistants = [
        {
            "id": assistant.id,
            "name": assistant.name,
            "instructions": assistant.instructions,
        }
        for assistant in assistants
    ]
    return assistants


@agent_action
def call_assistant(assistant_id, message):
    """Calls the assistant with the given assistant_id and message."""
    return api.call_assistant(assistant_id, message)


@agent_action
def create_assistant(
    assistant_name,
    assistant_instructions,
):
    """Creates an assistant with the given parameters.
    assistant_name: str, name of the assistant
    assistant_instructions: str, instructions for the assistant
    """
    actions_manager = ActionsManager()
    available_actions = actions_manager.get_actions()
    actions = [action["agent_action"] for action in available_actions]
    assistant = api.create_assistant(
        assistant_name,
        assistant_instructions,
        "gpt-4o",
        [],
        actions,
        "auto",
        1.0,
        1.0,
    )
    return assistant


@agent_action
def create_test_assistant():
    """Creates a test assistant."""
    return create_assistant("Test Assistant", "This is a test assistant.")


@agent_action
def create_manager_assistant():
    """Creates a manager assistant."""
    name = "Manager Assistant"
    instructions = """
    You are an assistant designed to manager other assistants. 
    To do so, you will need to call list_assistants every time a new conversation starts.  
    This will let you know which assistants you have access to and what they can do.   

    You will ALWAYS delegate user requests to the appropriate assistant you identified earlier using list_assistants. 
    Delegating a request can be done by using call_assistant.

    Use the following functions to test any code you receive:
    run_code to run all Python code before showing the user
    run_shell-command to install any required dependencies, example 'pip install pygame'
    """
    return create_assistant(name, instructions)
