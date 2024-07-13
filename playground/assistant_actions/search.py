import wikipedia

from playground.actions_manager import agent_action


@agent_action
def search_wikipedia(query):
    """
    Searches Wikipedia for the given query
    and returns a list of matching page_ids.
    """
    wikipedia.set_lang("en")
    search_results = wikipedia.search(query)
    return search_results


@agent_action
def get_wikipedia_summary(page_id):
    """
    Gets the summary of the Wikipedia page
    for the given page_id.
    """
    wikipedia.set_lang("en")
    summary = wikipedia.summary(page_id)
    return summary


@agent_action
def get_wikipedia_page(page_id):
    """
    Gets the full content of the
    Wikipedia page for the given page_id.
    """
    wikipedia.set_lang("en")
    page = wikipedia.page(page_id)
    return page.content
