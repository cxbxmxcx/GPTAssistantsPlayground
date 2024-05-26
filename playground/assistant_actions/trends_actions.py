from pytrends.request import TrendReq

from playground.actions_manager import agent_action


@agent_action
def get_google_trend_data(keywords):
    """Returns the Google trends trend data for the given keywords.
    keywords: list of keywords to search for.
    """
    # Connect to Google
    pytrends = TrendReq(hl="en-US", tz=360)

    if isinstance(keywords, str):
        if "," in keywords:
            keywords = keywords.split(",")
        else:
            keywords = [keywords]

    # Define the keywords
    kw_list = keywords

    # Build the payload
    pytrends.build_payload(kw_list, cat=0, timeframe="today 1-m", geo="", gprop="")

    # Get interest over time
    interest_over_time_df = pytrends.interest_over_time()

    return interest_over_time_df.to_string()
