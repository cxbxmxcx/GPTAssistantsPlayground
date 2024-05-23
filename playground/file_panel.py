import gradio as gr
import os
import json

# Directory to store JSON documents
DIRECTORY = 'json_documents'

# Ensure the directory exists
if not os.path.exists(DIRECTORY):
    os.makedirs(DIRECTORY)

# Helper functions
def list_documents():
    return [f[:-5] for f in os.listdir(DIRECTORY) if f.endswith('.json')]

def load_document(filename):
    filepath = os.path.join(DIRECTORY, f"{filename}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            return file.read()
    return "{}"

def save_document(filename, content):
    filepath = os.path.join(DIRECTORY, f"{filename}.json")
    with open(filepath, 'w') as file:
        file.write(content)
    return "Document saved successfully."

def delete_document(filename):
    filepath = os.path.join(DIRECTORY, f"{filename}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        return "Document deleted successfully."
    return "Document not found."

# Gradio interface functions
def update_editor(document_name):
    if document_name == "Create New Document":
        return gr.update(visible=True), gr.update(visible=True), "{}"
    else:
        return gr.update(visible=False), gr.update(visible=False), load_document(document_name)

def handle_save(document_name, new_document_name, content):
    if document_name == "Create New Document":
        if not new_document_name.strip():
            return "Please enter a valid document name.", gr.update(choices=["Create New Document"] + list_documents()), document_name
        document_name = new_document_name.strip()
    save_message = save_document(document_name, content)
    return save_message, gr.update(choices=["Create New Document"] + list_documents()), document_name

def handle_delete(document_name):
    delete_message = delete_document(document_name)
    return delete_message, gr.update(choices=["Create New Document"] + list_documents()), "Create New Document", "{}"

def file_panel():
    custom_css = """
        #delete_button {
            margin-top: -10px;
    """

    # Gradio components
    with gr.Blocks(css=custom_css) as file_panel:
        with gr.Row():
            with gr.Column(scale=8):
                document_dropdown = gr.Dropdown(choices=["Create New Document"] + list_documents(), label="Select document", value="Create New Document")
            with gr.Column(scale=1):
                save_button = gr.Button("💾", elem_id="save_button")        
                delete_button = gr.Button("🗑️", elem_id="delete_button")
        with gr.Row(visible=False) as new_doc_row:
            new_doc_name = gr.Textbox(label="New Document Name")
        json_editor = gr.Code(language='json', value="{}", label="JSON Editor", visible=False)
        message_display = gr.Markdown()

        document_dropdown.change(update_editor, [document_dropdown], [new_doc_row, new_doc_name, json_editor])
        save_button.click(handle_save, [document_dropdown, new_doc_name, json_editor], [message_display, document_dropdown, document_dropdown])
        delete_button.click(handle_delete, [document_dropdown], [message_display, document_dropdown, document_dropdown, json_editor])

    # demo.launch()
    return json_editor
