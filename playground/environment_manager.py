import os
import subprocess
import sys
from datetime import datetime
import time
import pyautogui


class EnvironmentManager:
    def __init__(self, base_path="environments", env_name="env"):
        self.base_path = base_path
        self.env_name = env_name
        self.env_path = os.path.join(self.base_path, self.env_name)
        self.ensure_directories()

    def ensure_directories(self):
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        if not os.path.exists(self.env_path):
            self.create_virtual_env()

    def create_virtual_env(self):
        subprocess.check_call([sys.executable, "-m", "venv", self.env_path])
        print(f"Created virtual environment at {self.env_path}")

    def install_requirements(self, requirements_file="code_env_requirements.txt"):
        pip_executable = (
            os.path.join(self.env_path, "Scripts", "pip")
            if os.name == "nt"
            else os.path.join(self.env_path, "bin", "pip")
        )
        subprocess.check_call([pip_executable, "install", "-r", requirements_file])
        print(f"Installed packages from {requirements_file}")

    def install_package(self, package):
        pip_executable = (
            os.path.join(self.env_path, "Scripts", "pip")
            if os.name == "nt"
            else os.path.join(self.env_path, "bin", "pip")
        )
        subprocess.check_call([pip_executable, "install", package])
        print(f"Installed package: {package}")

    def capture_screenshot(self, filename):
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)

    def run_app_file(self, filename):
        """
        Execute the specified Python web application file in a virtual environment.

        Args:
            filename (str, optional): The name of the file containing the web application code.

        Returns:
            tuple: A tuple containing:
                - initial_output (str): The initial output produced by the web application execution.
                - initial_errors (str): Any errors encountered during the initial web application execution.
        """
        if filename is None:
            raise ValueError("Filename must be provided")

        filepath = os.path.join(self.env_path, filename)
        python_executable = (
            os.path.join(self.env_path, "Scripts", "python")
            if os.name == "nt"
            else os.path.join(self.env_path, "bin", "python")
        )

        try:
            process = subprocess.Popen(
                [python_executable, filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Allow the process to run for a few seconds to capture initial output
            time.sleep(10)

            # Check if process has terminated
            return_code = process.poll()
            if return_code is not None:
                # Process terminated, capture output and errors
                initial_output, initial_errors = process.communicate()
            else:
                return "Process appears to be running correctly", ""

            return initial_output, initial_errors
        except Exception as e:
            return "", str(e)

    def run_code(self, code, filename=None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"code_{timestamp}.py"
        filepath = os.path.join(self.env_path, filename)

        if code is not None and code != "":
            # Write the code to a file
            with open(filepath, "w") as f:
                f.write(code)

        python_executable = (
            os.path.join(self.env_path, "Scripts", "python")
            if os.name == "nt"
            else os.path.join(self.env_path, "bin", "python")
        )

        # Start the subprocess
        process = subprocess.Popen(
            [python_executable, filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Allow some time for the Pygame window to open
        time.sleep(2)

        # Capture the initial screenshot
        self.capture_screenshot("initial_screenshot.png")

        # Wait for the process to complete
        stdout, stderr = process.communicate()

        # Capture the final screenshot
        self.capture_screenshot("final_screenshot.png")

        # Return the results
        if (stderr is None or stderr == "") and (stdout is None or stdout == ""):
            return "The process appears to have run successfully.", ""
        return stdout, stderr

    def run_shell_command(self, command):
        activate_script = (
            os.path.join(self.env_path, "Scripts", "activate")
            if os.name == "nt"
            else os.path.join(self.env_path, "bin", "activate")
        )
        if os.name == "nt":
            command = f'cmd /c "{activate_script} & {command}"'
        else:
            command = f'/bin/bash -c "source {activate_script} && {command}"'

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )
        # print(f"Output: {result.stdout}")
        # print(f"Errors: {result.stderr}")
        return result.stdout, result.stderr


# def main():
#     env_manager = EnvironmentManager()
#     env_manager.install_requirements()
#     code_output, code_errors = env_manager.run_code("print('Hello, World!')")
#     shell_output, shell_errors = env_manager.run_shell_command(
#         'echo "Running in shell"'
#     )


# if __name__ == "__main__":
#     main()
