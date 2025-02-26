import time

from prefect import flow
import py_trees

from playground.behavior_trees import (
    create_assistant_action,
)


@flow(log_prints=True)
def run_tree():
    # Create the root node (sequence)
    root = py_trees.composites.Sequence("RootSequence", memory=True)

    selector = py_trees.composites.Selector("Search Selector", memory=True)
    root.add_child(selector)

    def get_search_instructions():
        return """
                Use the function/tool get_search_term to load a search term from the list of search terms.            
                Query the "{search_term}" to search for "this week" videos on YouTube.
                Use the filter "this week" to search for videos on YouTube.
                then for each video download the transcript and determine relevance to the {search_term}
                then select a single video that is most relevant to the search term.
                Summarize the content of the video into 5 paragraphs,
                be sure to include a link to the video and highlight the link as a reference for the content.
                and then save the transcript summarizations to a file called youtube_transcripts.txt
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

    write_blog_action = create_assistant_action(
        action_name="Write blog",
        assistant_name="Medium Blogger",
        assistant_instructions="""
        Load the file called youtube_transcripts.txt,
        analyze the contents for references to the search term 
        at the top of the file and then select
        the most exciting and relevant content related to the search term but also: 
        educational, tutorial, informative, demonstation, to blog on Medium.    
        
        Write a blog in Word docx that is relevant to the content of the summarization,
        Be sure the blog captures the spirit of the themes and topic content,
        The name of the file should be {search term}_blog_{timestamp}.docx (You can get the timestamp using the get_current_timestamp() tool/function.)
        RULES:
        Avoid quoting individuals or organizations but rather generalize their statements.
        IMPORTANT: Be sure to add a reference to the video link in the blog post.
        Focus on new and innovative content.
        Be sure to highlight the technology theme/topic that was summarized.
        Make sure and add a compelling title for the blog post.
        
        At the top of the blog under the first section add the following disclainer in full:
        Disclaimer: this blog is entirely written by a team of agents including the images, layout and content. The process works by having the agents search, review and summarize the transcripts of YouTube videos, the summarized content is then written into a blog. If you want to understand more check out my book AI Agents In Action. My contribution is the selection of the stories to publish, copy/pasting content and writing the agents.
        As your last operation write the blog filename to a file called blog_filenames.txt.
        If you encounter any errors, please return just the word FAILURE.
        """,
    )
    root.add_child(write_blog_action)

    post_action = create_assistant_action(
        action_name="Post",
        assistant_name="Medium Post Writer",
        assistant_instructions="""
        Load the blog_filenames.txt file and to located Word docx file to load the blog content.
        Load the blog content for the Word docx file.  
        Write a post about the blog content for the following platforms: LinkedIn, Twitter, Reddit.   
        Save each of the post contents to a file called {word docx filename}_post_{platform name}.txt.
        If you encounter any errors, please return just the word FAILURE.
        """,
    )
    root.add_child(post_action)

    cleanup_action = create_assistant_action(
        action_name="Cleanup",
        assistant_name="File Manager",
        assistant_instructions="""
        Delete the youtube_transcripts.txt file.
        Delete the blog_filenames.txt file.      
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


if __name__ == "__main__":
    run_tree()
