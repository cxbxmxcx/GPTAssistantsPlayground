import os

from playground.actions_manager import agent_action
from playground.constants import ASSISTANTS_WORKING_FOLDER


@agent_action
def save_file(filename, content):
    """
    Save content to a file.

    :param filename: The name of the file including extension.
    :param content: The content to save in the file.
    """
    file_path = os.path.join(ASSISTANTS_WORKING_FOLDER, filename)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    return f"File '{filename}' saved successfully."


@agent_action
def load_file(filename):
    """
    Load content from a file.

    :param filename: The name of the file including extension.
    :return: The content of the file.
    """
    file_path = os.path.join(ASSISTANTS_WORKING_FOLDER, filename)
    if not os.path.exists(file_path):
        print(f"File '{filename}' does not exist.")
        return None

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    print(f"File '{filename}' loaded successfully.")
    return content


@agent_action
def delete_file(filename):
    """
    Delete a file.

    :param filename: The name of the file including extension.
    """
    file_path = os.path.join(ASSISTANTS_WORKING_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return f"File '{filename}' deleted successfully."
    else:
        return f"File '{filename}' does not exist."


@agent_action
def create_folder(foldername):
    """
    Create a folder.

    :param foldername: The name of the folder to create.
    """
    folder_path = os.path.join(ASSISTANTS_WORKING_FOLDER, foldername)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return f"Folder '{foldername}' created successfully."
    else:
        return f"Folder '{foldername}' already exists."


@agent_action
def list_files():
    """
    List all files in the working folder.

    :return: A list of file names.
    """
    files = os.listdir(ASSISTANTS_WORKING_FOLDER)
    return files


# # Example usage:
# if __name__ == "__main__":
#     # Save a file
#     save_file('example.txt', 'Hello, world!')

#     # Load a file
#     content = load_file('example.txt')
#     print(content)

#     # Delete a file
#     delete_file('example.txt')

#     # Create a folder
#     create_folder('example_folder')
