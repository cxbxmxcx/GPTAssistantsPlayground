import cv2
from moviepy.editor import VideoClip, concatenate_videoclips, VideoFileClip
from playground.actions_manager import agent_action
import os
from playground.constants import ASSISTANTS_WORKING_FOLDER


def safe_eval(expr):
    # Restrict eval to a safe subset of operations
    allowed_names = {"__builtins__": None}
    return eval(expr, allowed_names)


def convert_to_tuple(value):
    try:
        # Attempt to evaluate the string as a tuple
        evaluated_value = safe_eval(value)
        if isinstance(evaluated_value, tuple):
            return evaluated_value
        else:
            raise ValueError("The evaluated result is not a tuple")
    except (SyntaxError, NameError, ValueError) as e:
        print(f"Error evaluating value: {e}")
        return None


def convert_and_validate(value, image_dim):
    """
    Converts a string to its appropriate type and validates tuple values.
    Floats in the range 0-1 are converted to integers representing pixel locations.
    Integers are clamped within image dimensions.

    Args:
        value (str): The input value as a string.
        image_dim (tuple): The dimensions of the image (width, height).

    Returns:
        int, float, tuple: The converted and validated value.
    """
    if isinstance(value, str):
        value = convert_to_tuple(value)
    if isinstance(value, tuple):
        value = tuple(
            int(v * dim) if isinstance(v, float) and 0 <= v <= 1 else int(v)
            for v, dim in zip(value, image_dim)
        )
        value = (
            max(0, min(value[0], image_dim[0] - 1)),
            max(0, min(value[1], image_dim[1] - 1)),
        )
    elif isinstance(value, float) and 0 <= value <= 1:
        value = int(value * image_dim[0])
    return value


# Helper function to perform zoom
def zoom(image, zoom_factor, center=None):
    """
    Zooms into the image at a specified center point.

    Args:
        image (np.ndarray): The input image.
        zoom_factor (float): The zoom factor.
        center (tuple, optional): The center point for zooming. Defaults to the image center.

    Returns:
        np.ndarray: The zoomed image.
    """
    height, width, _ = image.shape
    image_dim = (width, height)
    if center:
        center = convert_and_validate(center, image_dim)
    elif center is None:
        center = (width / 2, height / 2)
    x, y = center
    radius_x, radius_y = int(width / (2 * zoom_factor)), int(height / (2 * zoom_factor))
    min_x, max_x = int(max(x - radius_x, 0)), int(min(x + radius_x, width))
    min_y, max_y = int(max(y - radius_y, 0)), int(min(y + radius_y, height))

    cropped = image[min_y:max_y, min_x:max_x]
    resized = cv2.resize(cropped, (width, height))
    return resized


@agent_action
def zoom_at(
    image_filename, duration, zoom_factor, output_filename, center=None, fps=30
):
    """
    Creates a zoom-in video clip from an image.

    Args:
        image_filename (str): Path to the input image.
        duration (int): Duration of the video in seconds.
        zoom_factor (float): Maximum zoom factor.
        output_filename (str): Path to save the output video.
        center (tuple, optional): Center point for zooming. Defaults to image center, is in pixels (512, 512) or as a ratio (0.5, 0.5).
        fps (int): Frames per second. Defaults to 30.

    Returns:
        str: Path to the saved video clip.
    """
    zoom_factor = float(zoom_factor)
    duration = int(duration)
    fps = int(fps)
    image_path = os.path.join(ASSISTANTS_WORKING_FOLDER, image_filename)
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width, _ = image.shape
    image_dim = (width, height)
    if center:
        center = convert_and_validate(center, image_dim)

    def make_frame(t):
        frame_num = int(t * fps)
        factor = 1 + (zoom_factor - 1) * frame_num / (fps * duration)
        return zoom(image, factor, center)

    clip = VideoClip(make_frame, duration=duration)

    output_path = os.path.join(ASSISTANTS_WORKING_FOLDER, output_filename)
    clip.write_videofile(output_path, fps=fps)
    return output_filename


@agent_action
def pan_to(image_filename, duration, start_center, end_center, output_filename, fps=30):
    """
    Creates a panning video clip from an image.

    Args:
        image_filename (str): Path to the input image.
        duration (int): Duration of the video in seconds.
        start_center (tuple): Starting center point for panning is in pixels (512, 512) or as a ratio (0.5, 0.5).
        end_center (tuple): Ending center point for panning is in pixels (512, 512) or as a ratio (0.5, 0.5).
        output_filename (str): Path to save the output video.
        fps (int): Frames per second. Defaults to 30.

    Returns:
        str: Path to the saved video clip.
    """
    duration = int(duration)
    fps = int(fps)

    image_path = os.path.join(ASSISTANTS_WORKING_FOLDER, image_filename)
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width, _ = image.shape
    image_dim = (width, height)
    start_center = convert_and_validate(start_center, image_dim)
    end_center = convert_and_validate(end_center, image_dim)

    def calculate_view_window(center, width, height):
        # Calculate maximum bounds while maintaining aspect ratio
        max_width = min(center[0], width - center[0])
        max_height = min(center[1], height - center[1])
        return int(max_width * 2), int(max_height * 2)

    # Calculate initial and final view window sizes
    initial_view_width, initial_view_height = calculate_view_window(
        start_center, width, height
    )
    final_view_width, final_view_height = calculate_view_window(
        end_center, width, height
    )

    def make_frame(t):
        frame_num = int(t * fps)
        x = int(
            start_center[0]
            + (end_center[0] - start_center[0]) * frame_num / (fps * duration)
        )
        y = int(
            start_center[1]
            + (end_center[1] - start_center[1]) * frame_num / (fps * duration)
        )
        # Calculate zoom level
        zoom_factor_x = initial_view_width + (
            final_view_width - initial_view_width
        ) * frame_num / (fps * duration)
        zoom_factor_y = initial_view_height + (
            final_view_height - initial_view_height
        ) * frame_num / (fps * duration)
        zoom_factor_x = max(1, zoom_factor_x)
        zoom_factor_y = max(1, zoom_factor_y)

        # Ensure the view window is within image boundaries
        left = max(0, x - int(zoom_factor_x / 2))
        right = min(width, x + int(zoom_factor_x / 2))
        top = max(0, y - int(zoom_factor_y / 2))
        bottom = min(height, y + int(zoom_factor_y / 2))

        # Extract the portion of the image
        frame = image[top:bottom, left:right]
        return cv2.resize(frame, (width, height))

    clip = VideoClip(make_frame, duration=duration)
    output_path = os.path.join(ASSISTANTS_WORKING_FOLDER, output_filename)
    clip.write_videofile(output_path, fps=fps)
    return output_filename


@agent_action
def zoom_from(
    image_filename, duration, zoom_factor, output_filename, center=None, fps=30
):
    """
    Creates a zoom-out video clip from an image.

    Args:
        image_filename (str): Path to the input image.
        duration (int): Duration of the video in seconds.
        zoom_factor (float): Initial zoom factor.
        output_filename (str): Path to save the output video.
        center (tuple, optional): Center point for zooming. Defaults to image center, is in pixels (512, 512) or as a ratio (0.5, 0.5).
        fps (int): Frames per second. Defaults to 30.

    Returns:
        str: Path to the saved video clip.
    """
    duration = int(duration)
    zoom_factor = float(zoom_factor)
    fps = int(fps)
    image_path = os.path.join(ASSISTANTS_WORKING_FOLDER, image_filename)
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width, _ = image.shape

    def make_frame(t):
        frame_num = int(t * fps)
        factor = zoom_factor - (zoom_factor - 1) * frame_num / (fps * duration)
        return zoom(image, factor, center)

    clip = VideoClip(make_frame, duration=duration)
    output_path = os.path.join(ASSISTANTS_WORKING_FOLDER, output_filename)
    clip.write_videofile(output_path, fps=fps)
    return output_filename


@agent_action
def boom_to(
    image_filename, duration, start_center, end_center, output_filename, fps=30
):
    """
    Creates a vertical panning video clip from an image.

    Args:
        image_filename (str): Path to the input image.
        duration (int): Duration of the video in seconds.
        start_center (tuple): Starting center point for vertical panning is in pixels (512, 512) or as a ratio (0.5, 0.5).
        end_center (tuple): Ending center point for vertical panning is in pixels (512, 512) or as a ratio (0.5, 0.5).
        output_filename (str): Path to save the output video.
        fps (int): Frames per second. Defaults to 30.

    Returns:
        str: Path to the saved video clip.
    """
    duration = int(duration)
    fps = int(fps)

    image_path = os.path.join(ASSISTANTS_WORKING_FOLDER, image_filename)
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width, _ = image.shape
    image_dim = (width, height)
    start_center = convert_and_validate(start_center, image_dim)
    end_center = convert_and_validate(end_center, image_dim)

    def make_frame(t):
        frame_num = int(t * fps)
        x = start_center[0]
        y = int(
            start_center[1]
            + (end_center[1] - start_center[1]) * frame_num / (fps * duration)
        )

        # Ensure the view window is within image boundaries
        left = max(0, x - width // 2)
        right = min(width, x + width // 2)
        top = max(0, y - height // 2)
        bottom = min(height + top, y + height // 2)
        # Extract the portion of the image
        frame = image[top:bottom, left:right]
        return cv2.resize(frame, (width, height))

    clip = VideoClip(make_frame, duration=duration)
    output_path = os.path.join(ASSISTANTS_WORKING_FOLDER, output_filename)
    clip.write_videofile(output_path, fps=fps)
    return output_filename


@agent_action
def rack_focus(image_filename, duration, start_blur, end_blur, output_filename, fps=30):
    """
    Creates a rack focus video clip from an image by changing the blur.

    Args:
        image_filename (str): Path to the input image.
        duration (int): Duration of the video in seconds.
        start_blur (int): Initial blur intensity.
        end_blur (int): Final blur intensity.
        output_filename (str): Path to save the output video.
        fps (int): Frames per second. Defaults to 30.

    Returns:
        str: Path to the saved video clip.
    """
    duration = int(duration)
    start_blur = int(start_blur)
    end_blur = int(end_blur)
    fps = int(fps)
    image_path = os.path.join(ASSISTANTS_WORKING_FOLDER, image_filename)
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width, _ = image.shape

    def make_frame(t):
        frame_num = int(t * fps)
        blur = int(start_blur + (end_blur - start_blur) * frame_num / (fps * duration))
        blur = max(1, blur // 2 * 2 + 1)  # Ensure blur is an odd integer greater than 0
        blurred_image = cv2.GaussianBlur(image, (blur, blur), 0)
        return blurred_image

    clip = VideoClip(make_frame, duration=duration)
    output_path = os.path.join(ASSISTANTS_WORKING_FOLDER, output_filename)
    clip.write_videofile(output_path, fps=fps)
    return output_filename


@agent_action
def whip_pan_to(
    image_filename, duration, start_center, end_center, output_filename, fps=30
):
    """
    Creates a whip pan video clip from an image.

    Args:
        image_filename (str): Path to the input image.
        duration (int): Duration of the video in seconds.
        start_center (tuple): Starting center point for panning is in pixels (512, 512) or as a ratio (0.5, 0.5).
        end_center (tuple): Ending center point for panning is in pixels (512, 512) or as a ratio (0.5, 0.5).
        output_filename (str): Path to save the output video.
        fps (int): Frames per second. Defaults to 30.

    Returns:
        str: Path to the saved video clip.
    """
    duration = int(duration)
    fps = int(fps)

    image_path = os.path.join(ASSISTANTS_WORKING_FOLDER, image_filename)
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width, _ = image.shape
    image_dim = (width, height)
    start_center = convert_and_validate(start_center, image_dim)
    end_center = convert_and_validate(end_center, image_dim)

    # def make_frame(t):
    #     frame_num = int(t * fps)
    #     if frame_num < fps * duration / 2:
    #         x = int(
    #             start_center[0]
    #             + (end_center[0] - start_center[0]) * frame_num / (fps * duration / 2)
    #         )
    #         y = start_center[1]
    #     else:
    #         x = end_center[0]
    #         y = int(
    #             start_center[1]
    #             + (end_center[1] - start_center[1])
    #             * (frame_num - fps * duration / 2)
    #             / (fps * duration / 2)
    #         )
    #     return zoom(image, 1, center=(x, y))
    def make_frame(t):
        frame_num = int(t * fps)
        y = start_center[1]
        x = int(
            start_center[0]
            + (end_center[0] - start_center[0]) * frame_num / (fps * duration)
        )

        # Ensure the view window is within image boundaries
        left = max(0, x - width // 2)
        right = min(width, x + width // 2)
        top = max(0, y - height // 2)
        bottom = min(height, y + height // 2)

        # Extract the portion of the image
        frame = image[top:bottom, left:right]
        return cv2.resize(frame, (width, height))

    clip = VideoClip(make_frame, duration=duration)
    output_path = os.path.join(ASSISTANTS_WORKING_FOLDER, output_filename)
    clip.write_videofile(output_path, fps=fps)
    return output_filename


@agent_action
def concatenate_clips(clip_filenames, output_filename, fps=30):
    """
    Concatenates a list of video clips into a single video.

    Args:
        clip_filenames (list): List of paths to video clips.
        output_filename (str): Path to save the concatenated video.
        fps (int): Frames per second. Defaults to 30.
    """
    if clip_filenames is None or len(clip_filenames) == 0:
        return "You need to specify a list of clips of at least length 1."
    if output_filename is None:
        return "You need to specify an output filename."

    fps = int(fps)
    clip_paths = [
        os.path.join(ASSISTANTS_WORKING_FOLDER, clip_path)
        for clip_path in clip_filenames
    ]
    clips = [VideoFileClip(clip_path) for clip_path in clip_paths]
    final_clip = concatenate_videoclips(clips)
    output_path = os.path.join(ASSISTANTS_WORKING_FOLDER, output_filename)
    final_clip.write_videofile(output_path, fps=fps)
    return f"{output_filename} created successfully."


# Example usage
# image_filename = 'image.png'

# # Load the image to get dimensions
# image = cv2.imread(image_filename)
# height, width, _ = image.shape

# # Generate clips and save them to files
# zoom_at_clip_path = zoom_at(image_filename, duration=3, zoom_factor=2, output_filename="zoom_at.mp4")
# pan_to_clip_path = pan_to(image_filename, duration=3, start_center=(width//2, height//2), end_center=(width//4, height//4), output_filename="pan_to.mp4")
# zoom_from_clip_path = zoom_from(image_filename, duration=3, zoom_factor=2, output_filename="zoom_from.mp4")
# boom_to_clip_path = boom_to(image_filename, duration=3, start_center=(width//2, height//2), end_center=(width//2, height//4), output_filename="boom_to.mp4")
# rack_focus_clip_path = rack_focus(image_filename, duration=3, start_blur=5, end_blur=15, output_filename="rack_focus.mp4")
# whip_pan_to_clip_path = whip_pan_to(image_filename, duration=3, start_center=(width//2, height//2), end_center=(width//4, height//4), output_filename="whip_pan_to.mp4")

# # Concatenate the clips
# concatenate_clips([zoom_at_clip_path, pan_to_clip_path, zoom_from_clip_path, boom_to_clip_path, rack_focus_clip_path, whip_pan_to_clip_path], output_filename="final_video.mp4")
