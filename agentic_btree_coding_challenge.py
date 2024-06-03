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
    Plant the Grass

    You will be given a matrix representing a field g and two numbers x, y coordinate.

    There are three types of possible characters in the matrix:

        x representing a rock.
        o representing a dirt space.
        + representing a grassed space.

    You have to simulate grass growing from the position (x, y). 
    Grass can grow in all four directions (up, left, right, down). 
    Grass can only grow on dirt spaces and can't go past rocks.

    Return the simulated matrix.
    Examples

    simulate_grass([
    "xxxxxxx",
    "xooooox",
    "xxxxoox"
    "xoooxxx"
    "xxxxxxx"
    ], 1, 1) ➞ [
    "xxxxxxx",
    "x+++++x",
    "xxxx++x"
    "xoooxxx"
    "xxxxxxx"
    ]

    Notes

    There will always be rocks on the perimeter
""")
judge_test_cases = textwrap.dedent("""
    Test.assert_equals(simulate_grass(["xxxxxxx","xooooox","xxxxoox","xoooxxx","xxxxxxx"], 1, 1), ["xxxxxxx","x+++++x","xxxx++x","xoooxxx","xxxxxxx"])
    Test.assert_equals(simulate_grass(["xxxxxxx","xoxooox","xxoooox","xooxxxx","xoxooox","xoxooox","xxxxxxx"], 2, 3), ["xxxxxxx","xox+++x","xx++++x","x++xxxx","x+xooox","x+xooox","xxxxxxx"])
    Test.assert_equals(simulate_grass(["xxxxxx","xoxoox","xxooox","xoooox","xoooox","xxxxxx"], 1, 1), ["xxxxxx","x+xoox","xxooox","xoooox","xoooox","xxxxxx"])
    Test.assert_equals(simulate_grass(["xxxxx","xooox","xooox","xooox","xxxxx"], 1, 1),["xxxxx","x+++x","x+++x","x+++x","xxxxx"])
    Test.assert_equals(simulate_grass(["xxxxxx","xxxxox","xxooox","xoooxx","xooxxx","xooxxx","xxooox","xxxoxx","xxxxxx"], 4, 1),["xxxxxx","xxxx+x","xx+++x","x+++xx","x++xxx","x++xxx","xx+++x","xxx+xx","xxxxxx"])
    Test.assert_equals(simulate_grass(["xxxxxxxxxxx", "xoxooooooox", "xoxoxxxxxox", "xoxoxoooxox", "xoxoxoxoxox", "xoxoxoxoxox", "xoxoxxxoxox", "xoxoooooxox", "xoxxxxxxxox", "xooooooooox", "xxxxxxxxxxx"], 1, 1), ["xxxxxxxxxxx", "x+x+++++++x", "x+x+xxxxx+x", "x+x+x+++x+x", "x+x+x+x+x+x", "x+x+x+x+x+x", "x+x+xxx+x+x", "x+x+++++x+x", "x+xxxxxxx+x", "x+++++++++x", "xxxxxxxxxxx"])   
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
