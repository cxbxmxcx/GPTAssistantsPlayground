import textwrap
import time

import py_trees

from playground.behavior_trees import (
    create_assistant_action_on_thread,
    create_assistant_condition_on_thread,
)
from playground.assistants_api import api

# Create the root node (sequence)
root = py_trees.composites.Sequence("RootSequence", memory=True)
bug_file = """
def add_numbers(num1, num2):    
    # Intentional error: '+' should be used instead of '-'
    return num1 - num2

def subtract_numbers(num1, num2):    
    return num1 - num2

def multiply_numbers(num1, num2):   
    return num3 * num2

def divide_numbers(num1, num2):    
    return num1 / num2

def main():
    print("Performing arithmetic operations with predefined values:")
    
    add_result = add_numbers()
    print(f"Addition Result: {add_result}")  
    
    subtract_result = subtract_numbers()
    print(f"Subtraction Result: {subtract_result}")  
    
    multiply_result = multiply_numbers()
    print(f"Multiplication Result: {multiply_result}")  
    
    divide_result = divide_numbers()
    print(f"Division Result: {divide_result}")  

if __name__ == "__main__":
    main()
"""

thread = api.create_thread()

debug_code = create_assistant_action_on_thread(
    thread=thread,
    action_name="Debug code",
    assistant_name="Python Debugger",
    assistant_instructions=textwrap.dedent(f"""    
    Here is the code with bugs in it:
    {bug_file}
    Run the code to identify the bugs and fix them. 
    Be sure to test the code to ensure it runs without errors or throws any exceptions.
    """),
)
root.add_child(debug_code)

verify = create_assistant_condition_on_thread(
    thread=thread,
    condition_name="Verify",
    assistant_name="Python Coding Assistant",
    assistant_instructions=textwrap.dedent(
        """
    Verify the solution fixes the bug and there are no more issues.
    Verify that no exceptions are thrown when the code is run.
    Reply with SUCCESS if the solution is correct, otherwise return FAILURE.
    If you are happy with the solution, save the code to a file called fixed_bug.py.
    """,
    ),
)
root.add_child(verify)


# Create the behavior tree
tree = py_trees.trees.BehaviourTree(root)

while True:
    tree.tick()
    time.sleep(20)  # Simulate time between ticks
    if root.status == py_trees.common.Status.SUCCESS:
        break
