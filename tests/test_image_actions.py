from playground.assistant_actions.image_actions import create_image


def test_create_image():
    image = create_image("a man walking on the street")
    assert image is not None
