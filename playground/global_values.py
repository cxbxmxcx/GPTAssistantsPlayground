import os


class GlobalValues:
    ASSISTANTS_WORKING_FOLDER = "assistants_working_folder"
    CODING_ENVIRONMENT_FOLDER = "environments/env"

    @classmethod
    def set_value(cls, var_name, value):
        if hasattr(cls, var_name):
            setattr(cls, var_name, value)
        else:
            raise AttributeError(f"{var_name} not found in GlobalValues")

    @classmethod
    def get_value(cls, var_name):
        if hasattr(cls, var_name):
            return getattr(cls, var_name)
        else:
            raise AttributeError(f"{var_name} not found in GlobalValues")


# Configure globals
class GlobalSetup:
    @staticmethod
    def setup_global_values():
        # Check and create directories
        working_folder = GlobalValues.get_value("ASSISTANTS_WORKING_FOLDER")
        if not os.path.exists(working_folder):
            os.makedirs(working_folder)
            print(f"Created folder: {working_folder}")


# Example usage
GlobalSetup.setup_global_values()
