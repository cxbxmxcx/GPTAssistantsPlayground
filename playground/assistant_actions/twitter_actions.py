import os
from twitter.account import Account

from playground.actions_manager import agent_action


@agent_action
def post_to_twitter(content):
    """Post a tweet to Twitter."""
    email = os.getenv("X_EMAIL")
    username = os.getenv("X_USERNAME")
    password = os.getenv("X_PASSWORD")
    account = Account(email, username, password)
    account.tweet(content)
    return f"Posted tweet: {content}"
