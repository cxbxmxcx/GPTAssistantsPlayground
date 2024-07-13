import random
import time

import py_trees

from playground.behavior_trees import (
    create_assistant_action,
)

# Create the root node (sequence)
root = py_trees.composites.Sequence("RootSequence", memory=True)

selector = py_trees.composites.Selector("Search Selector", memory=True)
root.add_child(selector)


def get_search_instructions(search_term):
    return f"""
            Search Term: {search_term}
            Use the query "{search_term}" to search for this weeks videos on YouTube. Set the publish time filter to "this week".    
            then for each video download the transcript and determine its relevance to the {search_term}
            From the collection of transcripts select a single common technology theme or topic that is relevant to the search term.
            Summarize the content that is relevant to the single technology theme/topic into 5 paragraphs,
            and then save all the summarized content to a file called youtube_transcripts.txt
            If you encounter any errors, please return just the word FAILURE.
            """


search_terms = [
    "AI Agents In Action",
    "AI Agents In Games",
    "AI News",
    "AI in Games",
    "AI Business News",
    "AI Music",
    "AI Video",
    "AI Startups",
    "AI Innovations and New Technolgoy",
    "AI in Medicine",
    "AI in Education",
    "AI in Agriculture",
    "AI in Transportation",
    "AI in Space",
    "AI in Robotics",
    "AI in Manufacturing",
    "AI in Retail",
    "AI in Finance",
    "AI in Sports",
    "AI in Entertainment",
    "AI in Art",
    "AI in Fashion",
    "AI in Travel",
    "AI in Environment",
    "AI in Energy",
    "AI in Security",
    "AI in Politics",
    "AI in Society",
    "AI in Health",
    "AI in Science",
    "AI in Technology",
    "AI in Engineering",
    "AI in Research",
    "AI in Software Development",
]

for i in range(10):
    search_term = random.choice(search_terms)
    search_terms.remove(search_term)
    search_youtube_action = create_assistant_action(
        action_name=f"Search YouTube({search_term})",
        assistant_name="YouTube Blog Researcher",
        assistant_instructions=get_search_instructions(search_term),
    )
    selector.add_child(search_youtube_action)

# search_term = "AI Agents In Games"
# search_youtube_action = create_assistant_action(
#     action_name=f"Search YouTube({search_term})",
#     assistant_name="YouTube Blog Researcher",
#     assistant_instructions=get_search_instructions(search_term),
# )
# selector.add_child(search_youtube_action)

# search_term = "AI News"
# search_youtube_action = create_assistant_action(
#     action_name=f"Search YouTube({search_term})",
#     assistant_name="YouTube Blog Researcher",
#     assistant_instructions=get_search_instructions(search_term),
# )
# selector.add_child(search_youtube_action)

write_blog_action = create_assistant_action(
    action_name="Write blog",
    assistant_name="Medium Blogger",
    assistant_instructions="""
    Load the file called youtube_transcripts.txt,
    analyze the contents for references to the search term 
    at the top of the file and then select
    the most exciting and relevant content related to the search term but also: 
    news, noteworthy, and informative, to blog on Medium.    
    
    Write a blog in Word docx that is relevant to the content of the summarizations,
    Be sure the blog captures the spirit of the themes and topic content,
    The name of the file should be {search term}_blog_{timestamp}.docx (You can get the timestamp using the get_current_timestamp() tool/function.)
    RULES:
    Avoid quoting individuals or organizations but rather generalize their statements.
    Focus on new and innovative content.
    Be sure to highlight the technology theme/topic that was summarized.
    Make sure and add a compelling title for the blog post.
    
    If you encounter any errors, please return just the word FAILURE.
    """,
)
root.add_child(write_blog_action)

post_action = create_assistant_action(
    action_name="Post",
    assistant_name="File Manager",
    assistant_instructions="""
    Delete the youtube_transcripts.txt file.      
    If you encounter any errors, please return just the word FAILURE.
    """,
)
root.add_child(post_action)


# Create the behavior tree
tree = py_trees.trees.BehaviourTree(root)

# Tick the tree to run it
while True:
    tree.tick()
    time.sleep(30)  # Simulate time between ticks
