from playground.actions_manager import agent_action


@agent_action
def get_reasoning(problem_text):
    """Generate a chain of thought reasoning strategy to solve the problem.
    Args:
        problem_text (str): The problem text to generate a reasoning strategy for.
    """
    return """
        Generate a chain of thought reasoning strategy 
        in order to solve the following problem. 
        Just output the reasoning steps and avoid coming
        to any conclusions. Also, be sure to avoid any assumptions
        and factor in potential unknowns.
"""


@agent_action
def get_feedback(result_text):
    """Generate feedback on the output of a tool or reply.
       Feedback can help align and imporve the quality of the output
    Args:
        result_text (str): The reasoning strategy generated.
    """
    return """
        Provide feedback on the generated results.
        Be sure to point out any potential flaws 
        in the reasoning used to generate the output
        and suggest ways to improve it.
"""
