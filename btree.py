import threading
import time

import py_trees

from playground.assistants_api import api


# Define the ActionWithThread class
class ActionWrapper(py_trees.behaviour.Behaviour):
    def __init__(self, name, action_function=None):
        super(ActionWrapper, self).__init__(name=name)
        self.thread = None
        self.thread_running = False
        self.thread_success = False
        self.action_function = action_function

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
            result = self.action_function()
            print(result)
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


# Create the root node (sequence)
root = py_trees.composites.Sequence("RootSequence", memory=True)

thread = api.create_thread()
assistant = api.get_assistant_by_name("manager")
message = "check the status of the thread, if there are no recent user messages, do nothing and return the word 'success'"

action_function = lambda: api.call_assistant_with_thread(thread, assistant.id, message)

# Create an instance of ActionWithThread and add it to the root node
long_running_action = ActionWithThread(
    name="LongRunningAction", action_function=action_function
)
root.add_child(long_running_action)

# Create the behavior tree
tree = py_trees.trees.BehaviourTree(root)

# Tick the tree to run it
for i in range(100):
    print(f"Tick {i + 1}")
    tree.tick()
    time.sleep(5)  # Simulate time between ticks

# Add a blackboard watcher to visualize the tree
# py_trees.display.render_dot_tree(tree.root)
