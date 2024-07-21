import threading


from prefect import task
import py_trees

from playground.assistants_api import api


# Define the FunctionWrapper class
class FunctionWrapper:
    def __init__(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        return self.function(*self.args, **self.kwargs)


# @task(log_prints=True)
# def init_wrapper(action):
#     # This is called once each time the behavior is started
#     print("%s.initialise()" % action.name)
#     action.thread_running = True
#     action.thread_success = False
#     action.thread = threading.Thread(target=action.long_running_process)
#     action.thread.start()


def create_task(action):
    @task(name=action.name, description=action.assistant_name, log_prints=True)
    def init_wrapper():
        print(f"Initializing task: {action.name}")
        print(f"Assistant: {action.assistant_name}")

        action.thread_running = True
        action.thread_success = False
        action.thread = threading.Thread(target=action.long_running_process)
        action.thread.start()

    return init_wrapper


# Define the ActionWithThread class
class ActionWrapper(py_trees.behaviour.Behaviour):
    def __init__(self, name, assistant_name, function_wrapper, is_condition=False):
        super(ActionWrapper, self).__init__(name=name)
        self.assistant_name = assistant_name
        self.thread = None
        self.thread_running = False
        self.thread_success = False
        self.function_wrapper = function_wrapper
        self.is_condition = is_condition

    def setup(self):
        # This is called once at the beginning to setup any necessary state or resources
        print("%s.setup()" % self.name)
        return py_trees.common.Status.SUCCESS

    def initialise(self):
        create_task(self)()
        # # This is called once each time the behavior is started
        # print("%s.initialise()" % self.name)
        # self.thread_running = True
        # self.thread_success = False
        # self.thread = threading.Thread(target=self.long_running_process)
        # self.thread.start()

    def long_running_process(self):
        try:
            print("%s: Thread started, running process..." % self.name)
            result = self.function_wrapper()
            print(result)
            if "FAILURE" in result["text"]:
                print("%s: Thread completed with failure." % self.name)
                return

            if self.is_condition:
                self.thread_success = "SUCCESS" in result["text"]
            else:
                self.thread_success = True

            print("%s: Thread completed successfully." % self.name)
        except Exception as e:
            print("%s: Exception in thread: %s" % (self.name, str(e)))
        finally:
            self.thread_running = False

    def update(self):
        # This is called every tick to update the status of the behavior
        print("%s.update()" % self.name)
        if self.thread_running:
            return py_trees.common.Status.RUNNING
        else:
            return (
                py_trees.common.Status.SUCCESS
                if self.thread_success
                else py_trees.common.Status.FAILURE
            )

    def terminate(self, new_status):
        # This is called once each time the behavior terminates
        print("%s.terminate(%s)" % (self.name, new_status))
        if self.thread is not None:
            self.thread.join()
        self.thread = None
        self.thread_running = False
        self.thread_success = False


def create_assistant_action(action_name, assistant_name, assistant_instructions):
    assistant = api.get_assistant_by_name(assistant_name)
    function_wrapper = FunctionWrapper(
        api.call_assistant, assistant.id, assistant_instructions
    )
    return ActionWrapper(
        name=action_name,
        assistant_name=assistant_name,
        function_wrapper=function_wrapper,
    )


def create_assistant_condition(condition_name, assistant_name, assistant_instructions):
    assistant = api.get_assistant_by_name(assistant_name)
    function_wrapper = FunctionWrapper(
        api.call_assistant, assistant.id, assistant_instructions
    )
    return ActionWrapper(
        name=condition_name,
        assistant_name=assistant_name,
        function_wrapper=function_wrapper,
        is_condition=True,
    )


def create_assistant_action_on_thread(
    thread, action_name, assistant_name, assistant_instructions
):
    assistant = api.get_assistant_by_name(assistant_name)
    function_wrapper = FunctionWrapper(
        api.call_assistant_with_thread, thread, assistant.id, assistant_instructions
    )
    return ActionWrapper(
        name=action_name,
        assistant_name=assistant_name,
        function_wrapper=function_wrapper,
    )


def create_assistant_condition_on_thread(
    thread, condition_name, assistant_name, assistant_instructions
):
    assistant = api.get_assistant_by_name(assistant_name)
    function_wrapper = FunctionWrapper(
        api.call_assistant_with_thread, thread, assistant.id, assistant_instructions
    )
    return ActionWrapper(
        name=condition_name,
        assistant_name=assistant_name,
        function_wrapper=function_wrapper,
        is_condition=True,
    )
