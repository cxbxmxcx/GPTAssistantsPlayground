import time

import py_trees

from playground.behavior_trees import (
    create_assistant_action,
)

# Create the root node (sequence)
root = py_trees.composites.Sequence("RootSequence", memory=True)

selector = py_trees.composites.Selector("Search Selector", memory=True)
root.add_child(selector)


def get_search_instructions():
    return """
            Use the function/tool get_search_term to load a search term from the list of search terms.            
            Query the "{search_term}" to search for "this week" videos on YouTube.
            Use the filter "this week" to search for videos on YouTube.
            then for each video download the transcript and summarize it for relevance to {search_term}
            be sure to include a link to each of the videos,
            and then save all the transcript summarizations to a file called youtube_transcripts.txt
            Make sure to save the search term at the top of the file.
            Always make sure to use save_file tool/function to save the file before moving on.
            If you encounter any errors, please return just the word FAILURE.
            """


search_youtube_action = create_assistant_action(
    action_name="Search YouTube",
    assistant_name="YouTube Researcher v3",
    assistant_instructions=get_search_instructions(),
)
selector.add_child(search_youtube_action)

write_post_action = create_assistant_action(
    action_name="Write Post",
    assistant_name="Twitter Post Writer",
    assistant_instructions="""
    Load the file called youtube_transcripts.txt,
    analyze the contents for references to search term at the top and then select
    the most exciting and relevant video related to: 
    eduction, tutorials, news or current events, to post on Twitter.
    Avoid any negative or controversial content.
    Avoid any content that is not relevant to the search term.
    Avoid content that promotes a business, jobs, real estate or investments.
    Then write a Twitter post that is relevant to the video,
    and always include a link to the video, along
    with exciting highlights or mentions, 
    and post it to the Twitter outbox.
    Remember to always include a link to the video and always
    use the post_to_twitter_outbox tool/function to post the content.
    If you encounter any errors, please return just the word FAILURE.
    """,
)
root.add_child(write_post_action)

cleanup_action = create_assistant_action(
    action_name="Cleanup",
    assistant_name="File Manager",
    assistant_instructions="""
    Delete the youtube_transcripts.txt file.      
    If you encounter any errors, please return just the word FAILURE.
    """,
)
root.add_child(cleanup_action)


# Create the behavior tree
tree = py_trees.trees.BehaviourTree(root)

# Tick the tree to run it
while True:
    tree.tick()
    time.sleep(30)  # Simulate time between ticks
