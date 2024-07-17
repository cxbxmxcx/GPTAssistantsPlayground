from playground.actions_manager import agent_action
from playground.environment_manager import EnvironmentManager


@agent_action
def run_python_code(code, filename=None):
    """
    Execute the provided Python code in a virtual environment.

    Args:
        code (str): The Python code to be executed.
        filename (str, optional): The name of the file containing the code. If provided,
                                  the code will be executed from this file. Defaults to None.

    Returns:
        tuple: A tuple containing two elements:
            - code_output (str): The standard output produced by the code execution.
            - code_errors (str): Any errors encountered during the code execution.
    """
    env_manager = EnvironmentManager()
    code_output, code_errors = env_manager.run_ode(code, filename=filename)
    return code_output, code_errors


@agent_action
def run_app_file(filename):
    """
    Execute the specified Python web application file in a virtual environment.

    Args:
        filename (str, optional): The name of the file containing the web application code.

    Returns:
        tuple: A tuple containing:
            - initial_output (str): The initial output produced by the web application execution.
            - initial_errors (str): Any errors encountered during the initial web application execution.
    """
    env_manager = EnvironmentManager()
    code_output, code_errors = env_manager.run_app_file(filename=filename)
    return code_output, code_errors


@agent_action
def run_shell_command(command):
    """Runs the given shell command in a virtual environment."""
    env_manager = EnvironmentManager()
    shell_output, shell_errors = env_manager.run_shell_command(command)
    return shell_output, shell_errors


@agent_action
def install_package(package):
    """Installs the given package in a virtual environment."""
    env_manager = EnvironmentManager()
    env_manager.install_package(package)
    return f"Installed package: {package}"
