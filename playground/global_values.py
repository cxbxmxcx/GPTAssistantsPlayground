class GlobalValues:
    ASSISTANTS_WORKING_FOLDER = "assistants_working_folder"

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
