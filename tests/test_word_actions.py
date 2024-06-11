from playground.assistant_actions.word_actions import extract_all_from_doc
from playground.global_values import GlobalValues
import os

# paths should be relative to the tests directory
path = __file__.replace("test_word_actions.py", "")
GlobalValues.set_value("ASSISTANTS_WORKING_FOLDER", os.path.join(path, "test_data"))


def test_extract_all_from_doc():
    doc_path = "test_document.docx"
    output_folder = "images"
    full_text, images, code_files = extract_all_from_doc(doc_path, output_folder)
    assert len(images) == 2
    assert len(full_text) > 0
    assert len(code_files) == 0
