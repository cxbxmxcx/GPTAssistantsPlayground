import time

import py_trees

from playground.behavior_trees import (
    create_assistant_action,
    create_assistant_condition,
)

search_term = "GPT Agents"
# Create the root node (sequence)
root = py_trees.composites.Sequence("RootSequence", memory=True)

file_condition = create_assistant_condition(
    condition_name="Check File Date",
    assistant_name="File Manager",
    assistant_instructions="""
    load the file youtube_current.txt.
    it will contain a date and time in the form HH-MM-DD-YY
    where HH (01-24) is the hour, DD is the month (01 - 31), MM is the day (01 - 12) and YY is the year (24)
    Return just the word SUCCESS if the date and time is earlier than the current date and time, 
    Return just the word FAILURE if the date and time is the same or later than the current date and time.
    """,
)
root.add_child(file_condition)

search_youtube_action = create_assistant_action(
    action_name="Search YouTube",
    assistant_name="YouTube Researcher",
    assistant_instructions=f"""
    Search Term: {search_term}
    Use the query "{search_term}" to search for videos on YouTube.
    then for each video download the transcript and summarize it for relevance to {search_term}
    be sure to include a link to each of the videos,
    and then save all summarizations to a file called youtube_transcripts.txt
    """,
)
root.add_child(search_youtube_action)

write_post_action = create_assistant_action(
    action_name="Write Post",
    assistant_name="Twitter Post Writer",
    assistant_instructions=f"""
    Load the file called youtube_transcripts.txt,
    analyze the contents for references to {search_term} and then select
    the most exciting and relevant video to post on Twitter.
    Then write a Twitter post that is relevant to the video,
    and include a link to the video, along
    with exciting highlights or mentions, 
    and save it to a file called youtube_twitter_post.txt.
    """,
)
root.add_child(write_post_action)

post_action = create_assistant_action(
    action_name="Post",
    assistant_name="Social Media Assistant",
    assistant_instructions="""
    Load the file called youtube_twitter_post.txt and post the content to Twitter.
    If the content is empty please do not post anything.
    """,
)
root.add_child(post_action)

file_write_action = create_assistant_action(
    action_name="Write File Date",
    assistant_name="File Manager",
    assistant_instructions="""
    write the current date and time to a file called youtube_current.txt.
    Format the date and time in the form HH-MM-DD-YY
    where HH (01-24) is the hour, DD is the month (01 - 31), MM is the day (01 - 12) and YY is the year (24)
    Be sure to increment the hour by 1 each time this action is called.    
    """,
)
root.add_child(file_write_action)

# Create the behavior tree
tree = py_trees.trees.BehaviourTree(root)

# Tick the tree to run it
for i in range(1000):
    print(f"Tick {i + 1}")
    tree.tick()
    time.sleep(300)  # Simulate time between ticks
