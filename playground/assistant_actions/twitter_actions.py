import os
from twitter.account import Account

from playground.actions_manager import agent_action


def create_twitter_account():
    """Create a Twitter account."""
    email = os.getenv("X_EMAIL")
    username = os.getenv("X_USERNAME")
    password = os.getenv("X_PASSWORD")
    account = Account(email, username, password)
    return account


account = create_twitter_account()


@agent_action
def post_to_twitter(content):
    """Post a tweet to Twitter."""
    account.tweet(content)
