import json

from playground.actions_manager import agent_action
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
