import textwrap
import time

import py_trees

from playground.behavior_trees import (
    create_assistant_action_on_thread,
    create_assistant_condition,
)
from playground.assistants_api import api

# Create the root node (sequence)
root = py_trees.composites.Sequence("RootSequence", memory=True)


thread = api.create_thread()
challenge = textwrap.dedent("""
    Given a string of digits, return the longest substring with alternating odd/even or even/odd digits. 
    If two or more substrings have the same length, return the substring that occurs first.
    Examples

    longest_substring("225424272163254474441338664823") ➞ "272163254"
    # substrings = 254, 272163254, 474, 41, 38, 23

    longest_substring("594127169973391692147228678476") ➞ "16921472"
    # substrings = 94127, 169, 16921472, 678, 476

    longest_substring("721449827599186159274227324466") ➞ "7214"
    # substrings = 7214, 498, 27, 18, 61, 9274, 27, 32
    # 7214 and 9274 have same length, but 7214 occurs first.

    Notes

    The minimum alternating substring size is 2, and there will always be at least one alternating substring.
""")
judge_test_cases = textwrap.dedent("""
    Test.assert_equals(longest_substring("844929328912985315632725682153"), "56327256")
    Test.assert_equals(longest_substring("769697538272129475593767931733"), "27212947")
    Test.assert_equals(longest_substring("937948289456111258444958189244"), "894561")
    Test.assert_equals(longest_substring("736237766362158694825822899262"), "636")
    Test.assert_equals(longest_substring("369715978955362655737322836233"), "369")
    Test.assert_equals(longest_substring("345724969853525333273796592356"), "496985")
    Test.assert_equals(longest_substring("548915548581127334254139969136"), "8581")
    Test.assert_equals(longest_substring("417922164857852157775176959188"), "78521")
    Test.assert_equals(longest_substring("251346385699223913113161144327"), "638569")
    Test.assert_equals(longest_substring("483563951878576456268539849244"), "18785")
    Test.assert_equals(longest_substring("853667717122615664748443484823"), "474")
    Test.assert_equals(longest_substring("398785511683322662883368457392"), "98785")
    Test.assert_equals(longest_substring("368293545763611759335443678239"), "76361")
    Test.assert_equals(longest_substring("775195358448494712934755311372"), "4947")
    Test.assert_equals(longest_substring("646113733929969155976523363762"), "76523")
    Test.assert_equals(longest_substring("575337321726324966478369152265"), "478369")
    Test.assert_equals(longest_substring("754388489999793138912431545258"), "545258")
    Test.assert_equals(longest_substring("198644286258141856918653955964"), "2581418569")
    Test.assert_equals(longest_substring("643349187319779695864213682274"), "349")
    Test.assert_equals(longest_substring("919331281193713636178478295857"), "36361")
    Test.assert_equals(longest_substring("2846286484444288886666448822244466688822247"), "47")    
""")

hacker = create_assistant_action_on_thread(
    thread=thread,
    action_name="Hacker",
    assistant_name="Python Coding Assistant",
    assistant_instructions=textwrap.dedent(f"""
    Challenge goal: 
    {challenge}
    Solve the challenge and output the final solution to a file called solution.py        
    """),
)
root.add_child(hacker)

judge = create_assistant_action_on_thread(
    thread=thread,
    action_name="Judge solution",
    assistant_name="Coding Challenge Judge",
    assistant_instructions=textwrap.dedent(
        f"""
    Challenge goal: 
    {challenge}
    Load the solution from the file solution.py.
    Then confirm is a solution to the challenge and test it with the following test cases:
    {judge_test_cases}  
    Run the code for the solution and confirm it passes all the test cases.
    If the solution passes all tests save the solution to a file called judged_solution.py
    """,
    ),
)
root.add_child(judge)

# verifier operates on a different thread, essentially in closed room
verifier = create_assistant_condition(
    condition_name="Verify solution",
    assistant_name="Python Coding Assistant",
    assistant_instructions=textwrap.dedent(
        f"""
    Challenge goal: 
    {challenge}
    Load the file called judged_solution.py and verify that the solution is correct by running the code and confirm it passes all the test cases:
    {judge_test_cases}
    If the solution is correct, return only the single word SUCCESS, otherwise return the single word FAILURE.
    """,
    ),
)
root.add_child(verifier)

# Create the behavior tree
tree = py_trees.trees.BehaviourTree(root)

# Tick the tree to run it
# for i in range(1000):
#     print(f"Tick {i + 1}")
#     tree.tick()
#     time.sleep(30)  # Simulate time between ticks

while True:
    tree.tick()
    time.sleep(20)  # Simulate time between ticks
    if root.status == py_trees.common.Status.SUCCESS:
        break
