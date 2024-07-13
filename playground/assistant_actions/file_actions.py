import os

from playground.actions_manager import agent_action
from playground.global_values import GlobalValues


@agent_action
def copy_file(source, destination):
    """
    Copy a file from the source to the destination.

    :param source: The source file path.
    :param destination: The destination file path.
    """
    if not os.path.exists(source):
        return f"Source file '{source}' does not exist."
    if os.path.exists(destination):
        return f"Destination file '{destination}' already exists."

    with open(source, "rb") as source_file:
        with open(destination, "wb") as destination_file:
            destination_file.write(source_file.read())
    return f"File '{source}' copied to '{destination}'."


@agent_action
def list_files(extension=None):
    """
    List all files in the working folder.

    :param extension: The file extension to filter by.
    :return: A list of file names.
    """
    files = os.listdir(GlobalValues.ASSISTANTS_WORKING_FOLDER)
    if extension:
        files = [file for file in files if file.endswith(extension)]
    return files


@agent_action
def save_file(filename, content):
    """
    Save content to a file.

    :param filename: The name of the file including extension.
    :param content: The content to save in the file.
    """
    file_path = os.path.join(GlobalValues.ASSISTANTS_WORKING_FOLDER, filename)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    return f"File '{filename}' saved successfully."


@agent_action
def save_code_file(filename, code):
    """
    Save code to a file.

    :param filename: The name of the file including extension.
    :param code: The code to save in the file.
    """
    file_path = os.path.join(GlobalValues.CODING_ENVIRONMENT_FOLDER, filename)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(code)
    return f"File '{filename}' saved successfully."


@agent_action
def load_file(filename):
    """
    Load content from a file.

    :param filename: The name of the file including extension.
    :return: The content of the file.
    """
    file_path = os.path.join(GlobalValues.ASSISTANTS_WORKING_FOLDER, filename)
    if not os.path.exists(file_path):
        print(f"File '{filename}' does not exist.")
        return None

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    print(f"File '{filename}' loaded successfully.")
    return content


@agent_action
def load_code_file(filename):
    """
    Load code from a file.

    :param filename: The name of the file including extension.
    :return: The code from the file.
    """
    file_path = os.path.join(GlobalValues.CODING_ENVIRONMENT_FOLDER, filename)
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
    file_path = os.path.join(GlobalValues.ASSISTANTS_WORKING_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return f"File '{filename}' deleted successfully."
    else:
        return f"File '{filename}' does not exist."


@agent_action
def delete_code_file(filename):
    """
    Delete a code file.

    :param filename: The name of the file including extension.
    """
    file_path = os.path.join(GlobalValues.CODING_ENVIRONMENT_FOLDER, filename)
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
    folder_path = os.path.join(GlobalValues.ASSISTANTS_WORKING_FOLDER, foldername)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return f"Folder '{foldername}' created successfully."
    else:
        return f"Folder '{foldername}' already exists."


@agent_action
def create_code_folder(foldername):
    """
    Create a folder in the coding environment folder.

    :param foldername: The name of the folder to create.
    """
    folder_path = os.path.join(GlobalValues.CODING_ENVIRONMENT_FOLDER, foldername)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return f"Folder '{foldername}' created successfully."
    else:
        return f"Folder '{foldername}' already exists."


@agent_action
def list_code_files():
    """
    List all code files in the coding environment folder.

    :return: A list of file names.
    """
    files = os.listdir(GlobalValues.CODING_ENVIRONMENT_FOLDER)
    return files


@agent_action
def set_working_folder(foldername):
    """
    Set the working folder for file operations.

    :param foldername: The name of the folder to set as the working folder.
    """
    GlobalValues.set_value("ASSISTANTS_WORKING_FOLDER", foldername)
    return f"Working folder set to '{foldername}'."


@agent_action
def set_working_code_folder(foldername):
    """
    Set the working folder for the code environment operations.

    :param foldername: The name of the folder to set as the coding environment folder.
    """
    GlobalValues.set_value("CODING_ENVIRONMENT_FOLDER", foldername)
    return f"Coding environment folder set to '{foldername}'."


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
