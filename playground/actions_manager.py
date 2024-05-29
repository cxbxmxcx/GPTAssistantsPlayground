import ast
import functools
import importlib.util
import inspect
import os
import threading


def handle_semantic_function_call(prompt, agent):
    system, user = parse_prompt(prompt)
    response = agent.get_semantic_response(system, user)
    return response


def parse_prompt(prompt):
    # Prepare the dictionary to hold the parsed contents
    parsed_contents = {"System": "", "User": ""}

    # Current section being parsed
    current_section = None

    # Split the docstring into lines and iterate through them
    for line in prompt.split("\n"):
        # Check if the line marks the beginning of a section
        if line.strip().startswith("System:"):
            current_section = "System"
            continue  # Skip the current line to avoid including the section identifier
        elif line.strip().startswith("User:"):
            current_section = "User"
            continue  # Skip the current line to avoid including the section identifier

        # Add the line to the current section if it's not None
        if current_section:
            # Add the line to the appropriate section, maintaining line breaks for readability
            parsed_contents[current_section] += line.strip() + "\n"

    # Trim the trailing newlines from each section's content
    for key in parsed_contents:
        parsed_contents[key] = parsed_contents[key].rstrip("\n")

    return parsed_contents["System"], parsed_contents["User"]


def agent_action(func):
    @functools.wraps(func)
    def wrapper(*args, _caller_agent=None, **kwargs):
        # Check if _prompt_template is set and format the prompt
        if hasattr(wrapper, "_prompt_template") and _caller_agent:
            # Adjust the template from double to single curly braces for formatting
            adjusted_template = wrapper._prompt_template.replace("{{", "{").replace(
                "}}", "}"
            )
            # Format the template with the arguments
            prompt = adjusted_template.format(*args, **kwargs)
            # Here, instead of directly returning, you can now use 'prompt' as needed
            # For demonstration, let's print it or you can return it
            print(prompt)  # or return prompt if that's your intent
            return handle_semantic_function_call(prompt, _caller_agent)
        else:
            # Proceed with the original call
            return func(*args, **kwargs)

    # Inspect the function's signature
    sig = inspect.signature(func)
    params = sig.parameters.values()

    # Construct properties and required fields
    properties = {}
    required = []
    for param in params:
        # Determine if the parameter has a default value
        if param.default is inspect.Parameter.empty:
            required.append(param.name)
            properties[param.name] = {
                "type": "string",  # Default type for demonstration; could be enhanced to infer actual type
                "description": param.name,  # Placeholder description; could be enhanced with actual docstrings
            }
        else:
            # Enum handling for specific cases (like 'unit' in your example)
            if param.name == "unit":
                properties[param.name] = {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit",
                }
            else:
                properties[param.name] = {
                    "type": "string",  # As above, simplified type handling
                    "description": param.name,  # Placeholder description
                }

    # Construct the OpenAI function specification
    func_spec = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }

    # If the function is a semantic function, add the prompt template from the docstring
    if "{{" in func.__doc__ and "}}" in func.__doc__:
        prompt_template = func.__doc__
        wrapper._prompt_template = prompt_template

    wrapper._agent_action = func_spec
    return wrapper


class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with threading.Lock():
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class ActionsManager(metaclass=SingletonMeta):
    def __init__(self):
        self.actions = []  # Initialize an empty list to store actions
        self.actions_folder = os.path.join(
            os.path.dirname(__file__), "assistant_actions"
        )
        self.collect_and_update_actions()

    def add_action(self, action):
        """Manually add a function specification."""
        self.actions.append(action)

    def get_actions(self):
        """Retrieve all stored function specifications."""
        return self.actions

    def get_action(self, action_name):
        """Retrieve a specific stored function specification."""
        for action in self.actions:
            if action["name"] == action_name:
                return action
        return None

    def get_action_names(self):
        """Retrieve the names of all stored actions."""
        return [action["name"] for action in self.actions]

    def collect_and_update_actions(self):
        """Collect and update actions with function pointers from Python files in the specified folder."""
        self.actions = []  # Reset actions list to ensure it's fresh on each call
        for root, dirs, files in os.walk(self.actions_folder):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    with open(full_path, "r", encoding="utf-8") as f:
                        file_contents = f.read()
                    self.actions.extend(
                        self.inspect_file_for_decorated_actions(
                            file_contents, full_path
                        )
                    )

    def inspect_file_for_decorated_actions(self, file_contents, full_path):
        """Inspect file contents for functions decorated with `agent_action` and load them."""
        tree = ast.parse(file_contents)
        decorated_actions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if (
                        isinstance(decorator, ast.Name)
                        and decorator.id == "agent_action"
                    ) or (
                        isinstance(decorator, ast.Attribute)
                        and decorator.attr == "agent_action"
                    ):
                        # Dynamically load the function and update the action with its pointer
                        function_pointer = self.load_function(full_path, node.name)
                        decorated_actions.append(
                            {
                                "name": node.name,
                                "group": os.path.splitext(os.path.basename(full_path))[
                                    0
                                ],
                                "pointer": function_pointer,
                                "agent_action": getattr(
                                    function_pointer, "_agent_action", None
                                ),
                                "prompt_template": getattr(
                                    function_pointer, "_prompt_template", None
                                ),
                            }
                        )
        return decorated_actions

    def load_function(self, module_path, function_name):
        """Dynamically load a function from a given module path."""
        spec = importlib.util.spec_from_file_location("module.name", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, function_name)
