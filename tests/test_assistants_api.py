import pytest

from playground.actions_manager import ActionsManager
from playground.assistants_api import AssistantsAPI


@pytest.fixture
def api():
    return AssistantsAPI()


def test_api_get_assistants(api):
    assistants = api.list_assistants()
    assert len(assistants.data) > 0


def test_api_create_assistant_code(api):
    name = "Test Assistant"
    instructions = "This is a test assistant"
    model = "gpt-4o"
    tools = [{"type": "code_interpreter"}]
    actions = None
    response_format = "auto"
    temperature = 1.0
    top_p = 1.0
    assistant = api.create_assistant(
        name, instructions, model, tools, actions, response_format, temperature, top_p
    )

    assert assistant.name == name
    assert assistant.instructions == instructions
    assert assistant.model == model
    assert assistant.tools is not None

    assert assistant.response_format == response_format
    assert assistant.temperature == temperature

    assert assistant.top_p == top_p


def test_api_create_assistant_custom_actions(api):
    name = "Test Assistant"
    instructions = "This is a test assistant"
    model = "gpt-4o"
    tools = [{"type": "code_interpreter"}]
    actions = [
        {
            "type": "function",
            "function": {
                "name": "get_current_temperature",
                "description": "Get the current temperature for a specific location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g., San Francisco, CA",
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["Celsius", "Fahrenheit"],
                            "description": "The temperature unit to use. Infer this from the user's location.",
                        },
                    },
                    "required": ["location", "unit"],
                },
            },
        }
    ]
    response_format = "auto"
    temperature = 1.0
    top_p = 1.0

    assistant = api.create_assistant(
        name, instructions, model, tools, actions, response_format, temperature, top_p
    )

    assert assistant.name == name
    assert assistant.instructions == instructions
    assert assistant.model == model
    assert assistant.tools is not None

    assert assistant.response_format == response_format
    assert assistant.temperature == temperature
    assert assistant.top_p == top_p


def test_action_manager_create_assistant(api):
    actions_manager = ActionsManager()
    available_actions = actions_manager.get_actions()
    actions = [action["agent_action"] for action in available_actions]

    name = "Test Action Assistant"
    instructions = "This is a test assistant"
    model = "gpt-4o"
    tools = [{"type": "code_interpreter"}]
    response_format = "auto"
    temperature = 1.0
    top_p = 1.0
    assistant = api.create_assistant(
        name, instructions, model, tools, actions, response_format, temperature, top_p
    )

    assert assistant.name == name
    assert assistant.instructions == instructions
    assert assistant.model == model
    assert assistant.tools is not None

    assert assistant.response_format == response_format
    assert assistant.temperature == temperature

    assert assistant.top_p == top_p


def text_create_assistant_with_actions(api):
    pass


def test_delete_test_assistants(api):
    assistants = api.list_assistants()
    for assistant in assistants.data:
        if assistant.name.startswith("Test"):
            api.delete_assistant(assistant.id)
    assistants = api.list_assistants()
    assert len(assistants.data) > 0


def test_call_assistant(api):
    assistants = api.list_assistants()
    assistant = assistants.data[0]
    response = api.call_assistant(assistant.id, "Hello, world!")
    assert response is not None
    assert response.text is not None
    assert response.text != ""
