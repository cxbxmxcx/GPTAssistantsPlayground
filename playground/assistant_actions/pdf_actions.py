import fitz  # PyMuPDF
from PIL import Image
import io
import os

from playground.actions_manager import agent_action
from playground.global_values import GlobalValues


@agent_action
def extract_images_text_from_pdf(pdf_path):
    """
    Extracts text and images from a PDF file.

    Args:
        pdf_path (str): The file path to the PDF document.

    Returns:
        tuple: A tuple containing:
            - str: The full text extracted from the PDF.
            - list: A list of file paths to the extracted images.
    """
    # Open the PDF file
    pdf_name = os.path.basename(pdf_path)
    pdf_path = os.path.join(GlobalValues.ASSISTANTS_WORKING_FOLDER, pdf_path)
    document = fitz.open(pdf_path)
    full_text = ""
    image_paths = []

    # Create a directory to save the images
    base_dir = os.path.dirname(pdf_path)
    images_dir = os.path.join(base_dir, f"{pdf_name}_images")
    os.makedirs(images_dir, exist_ok=True)

    # Process each page
    for page_num in range(len(document)):
        page = document.load_page(page_num)

        # Extract text
        text = page.get_text()
        full_text += f"Page {page_num+1}:\n{text}\n"

        # Extract images
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = document.extract_image(xref)
            image_bytes = base_image["image"]

            # Save the image
            image = Image.open(io.BytesIO(image_bytes))
            image = image.convert("RGB")
            image = image.resize((1024, 1024), Image.LANCZOS)
            image_filename = f"page_{page_num+1}_image_{img_index+1}.png"
            image_path = os.path.join(images_dir, image_filename)

            # Save the resized image
            image.save(image_path, format="PNG")
            image_paths.append(image_path)

    return full_text, image_paths


# Example usage
# pdf_path = 'path/to/your/pdf_file.pdf'
# text, images = extract_images_text_from_pdf(pdf_path)
# print("Extracted Text:", text)
# print("Extracted Images:", images)
