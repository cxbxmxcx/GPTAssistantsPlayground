import json

from playground.actions_manager import ActionsManager, agent_action
from playground.assistants_api import api
import os


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
def list_all_working_files():
    """Lists all the uploaded files for the given purpose."""
    files = api.list_files(purpose=None).data
    files = [
        {"id": file.id, "filename": file.filename, "purpose": file.purpose}
        for file in files
    ]
    return json.dumps(files)


@agent_action
def download_working_file_and_save(file_id, filename):
    """Downloads the file with the given file_id and saves it with the given name."""
    if file_id is None:
        return "You must supply a file_id to download."

    file = api.retrieve_file(file_id)
    if not file:
        return f"Unable to retrieve file with ID {file_id}."
    with open(filename, "wb") as f:
        f.write(file.content)
    return f"File with ID {file_id} downloaded and saved as {filename}."


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


def get_tools(tools):
    """Get the tools from the given tools list."""
    tools_list = []
    for tool in tools:
        if hasattr(tool, "name"):
            tools_list.append(tool["name"])
        elif hasattr(tool, "function"):
            tools_list.append(tool.function.name)
        elif hasattr(tool, "type"):
            tools_list.append(tool.type)
    return tools_list


@agent_action
def get_assistant_as_json(assistant_id):
    """Get the assistant with the given assistant_id as a JSON string."""
    assistant = api.retrieve_assistant(assistant_id)
    if not assistant:
        return f"Unable to retrieve assistant with ID {assistant_id}."
    name = assistant.name
    instructions = assistant.instructions
    model = assistant.model
    tools = get_tools(assistant.tools)
    response_format = assistant.response_format
    temperature = assistant.temperature
    top_p = assistant.top_p
    assistant = {
        "id": assistant_id,
        "name": name,
        "instructions": instructions,
        "model": model,
        "tools": tools,
        "response_format": response_format,
        "temperature": temperature,
        "top_p": top_p,
    }
    return json.dumps(assistant)


@agent_action
def list_installable_assistants():
    """Lists all the installable assistants."""
    filepath = os.path.join(os.path.dirname(__file__), "assistants.json")
    with open(filepath, "r", encoding="utf-8") as file:
        assistants = json.load(file)
    return assistants


@agent_action
def call_assistant(assistant_id, message):
    """Calls the assistant with the given assistant_id and message."""
    return api.call_assistant(assistant_id, message)


@agent_action
def create_assistant(
    assistant_name,
    assistant_instructions,
    model,
    tools,
    response_format,
    temperature,
    top_p,
):
    """Creates an assistant with the given parameters.
    assistant_name: str, name of the assistant
    assistant_instructions: str, instructions for the assistant
    model: str, model to use for the assistant
    tools: list, list of tools to use for the assistant
    response_format: str, response format for the assistant
    temperature: float, temperature for the assistant
    top_p: float, top p value for the assistant
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
    """
    return create_assistant(name, instructions)
