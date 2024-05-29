import os

from playground.actions_manager import agent_action

OUTPUT_FOLDER = "assistant_outputs"


@agent_action
def save_file(filename, content):
    """
    Save content to a file.

    :param filename: The name of the file including extension.
    :param content: The content to save in the file.
    """
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"File '{filename}' saved successfully.")


@agent_action
def load_file(filename):
    """
    Load content from a file.

    :param filename: The name of the file including extension.
    :return: The content of the file.
    """
    file_path = os.path.join(OUTPUT_FOLDER, filename)
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
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File '{filename}' deleted successfully.")
    else:
        print(f"File '{filename}' does not exist.")


@agent_action
def create_folder(foldername):
    """
    Create a folder.

    :param foldername: The name of the folder to create.
    """
    folder_path = os.path.join(OUTPUT_FOLDER, foldername)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{foldername}' created successfully.")
    else:
        print(f"Folder '{foldername}' already exists.")


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
