import os
import requests
import fal_client
import time
import hashlib

from playground.actions_manager import agent_action
from playground.global_values import GlobalValues


@agent_action
def create_image_with_fal(
    prompt,
    model="fal-ai/flux-pro",
    image_size="landscape_4_3",
    num_inference_steps=28,
    guidance_scale=20.0,
    seed=222,
):
    """
    Generates an image using the FAL model service and downloads it to a local directory.

    Args:
        prompt (str): The text prompt to generate the image.
        model (str, optional): The FAL model identifier to use for image generation. Default is "fal-ai/flux-pro".
        image_size (str, optional): The desired image size. Default is "landscape_4_3".
        num_inference_steps (int, optional): The number of inference steps for image generation. Default is 28.
        guidance_scale (float, optional): The guidance scale for image generation. Default is 3.5.
        seed: The seed used to as the randomized input into the model

    Returns:
        str: The local filename of the downloaded image if successful.

    """
    try:
        seed = int(seed)
        handler = fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "image_size": image_size,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "num_images": 1,
                "safety_tolerance": "2",
                "seed": seed,
            },
        )

        result = handler.get()
        image_url = result["images"][0]["url"]
        print(image_url)
    except Exception as e:
        return str(e)

    # Generate a unique filename
    timestamp = int(time.time())
    hash_object = hashlib.md5(
        f"{prompt}{model}{guidance_scale}{num_inference_steps}{timestamp}".encode()
    )
    unique_id = hash_object.hexdigest()[:8]

    # Format the filename
    local_filename = f"{prompt.replace(' ', '_').replace(',', '')[:20]}_{model.replace('/', '_')}_{guidance_scale}_{num_inference_steps}_{unique_id}.png"
    local_path = os.path.join(GlobalValues.ASSISTANTS_WORKING_FOLDER, local_filename)

    # Download the image
    image_response = requests.get(image_url)
    if image_response.status_code == 200:
        with open(local_path, "wb") as f:
            f.write(image_response.content)
        return local_filename
    else:
        raise Exception(
            f"Failed to download image, status code: {image_response.status_code}"
        )
