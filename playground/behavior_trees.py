import threading


import py_trees

from playground.assistants_api import api
import agentops


# Define the FunctionWrapper class
class FunctionWrapper:
    def __init__(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        return self.function(*self.args, **self.kwargs)


# Define the ActionWithThread class
class ActionWrapper(py_trees.behaviour.Behaviour):
    def __init__(self, name, function_wrapper, is_condition=False):
        super(ActionWrapper, self).__init__(name=name)
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
        # This is called once each time the behavior is started
        print("%s.initialise()" % self.name)
        self.thread_running = True
        self.thread_success = False
        self.thread = threading.Thread(target=self.long_running_process)
        self.thread.start()

    def long_running_process(self):
        # Simulate a long-running process
        try:
            print("%s: Thread started, running process..." % self.name)
            agentops.init()
            agentops.start_session()
            result = self.function_wrapper()
            print(result)
            if "FAILURE" in result["text"]:
                agentops.end_session("Fail")
                print("%s: Thread completed with failure." % self.name)
                return

            if self.is_condition:
                self.thread_success = "SUCCESS" in result["text"]
            else:
                self.thread_success = True

            agentops.end_session("Success")
            print("%s: Thread completed successfully." % self.name)
        except Exception as e:
            print("%s: Exception in thread: %s" % (self.name, str(e)))
            agentops.end_session("Fail")
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
    return ActionWrapper(name=action_name, function_wrapper=function_wrapper)


def create_assistant_condition(condition_name, assistant_name, assistant_instructions):
    assistant = api.get_assistant_by_name(assistant_name)
    function_wrapper = FunctionWrapper(
        api.call_assistant, assistant.id, assistant_instructions
    )
    return ActionWrapper(
        name=condition_name, function_wrapper=function_wrapper, is_condition=True
    )
