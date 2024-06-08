import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import base64

from playground.actions_manager import agent_action
from playground.global_values import GlobalValues

load_dotenv()

client = OpenAI()


@agent_action
def create_image(prompt, model="dall-e-3", size="1024x1024", quality="standard", n=1):
    """
    Generate an image based on the provided prompt using the DALL-E model.
    Args:
        prompt (str): The prompt used to generate the image.
        model (str, optional): The model used to generate the image. Defaults to "dall-e-3".
        size (str, optional): The size of the image in pixels. Defaults to "1024x1024". Options are 1024x1024, 1024x1792 or 1792x1024.
        quality (str, optional): The quality of the generation. Defaults to "standard". Options are "standard" or "hd" for high definition.
        n (int, optional): The number of generations. Defaults to 1. Always 1 for now.
    Returns:
        str: The path to the generated image file.
    """

    try:
        response = client.images.generate(
            model=model, prompt=prompt, size=size, quality=quality, n=n
        )
        image_url = response.data[0].url
    except Exception as e:
        return str(e)

    # Download the image
    image_response = requests.get(image_url)
    if image_response.status_code == 200:
        local_filename = f"{prompt.replace(' ', '_').replace(',','')[:50]}.png"
        local_path = os.path.join(
            GlobalValues.ASSISTANTS_WORKING_FOLDER, local_filename
        )
        with open(local_path, "wb") as f:
            f.write(image_response.content)
        return local_filename
    else:
        raise Exception(
            f"Failed to download image, status code: {image_response.status_code}"
        )


def encode_image(image_filename):
    """
    Encode the image to base64 format.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The base64 encoded string of the image.
    """
    local_path = os.path.join(GlobalValues.ASSISTANTS_WORKING_FOLDER, image_filename)
    if not os.path.exists(local_path):
        return f"File not found: {image_filename}"
    with open(local_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


@agent_action
def describe_image(
    image_filename,
    model="gpt-4o",
    prompt="""
    Describe exactly what is in the image and locate the objects in the image relative to its position.
    e.g. "There is a cat sitting on the table in the bottom right of the image."
    """,
    max_tokens=512,
):
    """
    Describe the content of an image using the OpenAI API.

    Args:
        image_path (str): The path to the image file.
        model (str, optional): The model to use for the OpenAI API. Defaults to "gpt-4o".
        prompt (str, optional): The prompt to describe the image. Defaults to 'Describe exactly what is in the image and locate the objects in the image relative to its position. e.g. "There is a cat sitting on the table in the bottom right of the image.'.
        max_tokens (int, optional): The maximum number of tokens for the response. Defaults to 512.

    Returns:
        dict: The response from the OpenAI API.
    """
    # Getting the base64 string
    base64_image = encode_image(image_filename)
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
        "max_tokens": max_tokens,
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
    )

    return response.json()
