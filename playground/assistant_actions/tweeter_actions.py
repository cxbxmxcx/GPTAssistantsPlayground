import random
import urllib.parse
import json
from peewee import SqliteDatabase, Model, IntegerField, TextField

from playground.actions_manager import agent_action

# Initialize Peewee database
db = SqliteDatabase("tweets.db")


class Tweet(Model):
    id = IntegerField(primary_key=True)
    content = TextField()

    class Meta:
        database = db


db.connect()
db.create_tables([Tweet])


class TweetManager:
    @staticmethod
    def get_all_tweets():
        tweets = Tweet.select()
        return [(tweet.id, tweet.content) for tweet in tweets]

    @staticmethod
    def add_tweet(content):
        Tweet.create(content=content)

    @staticmethod
    def update_tweet(tweet_id, content):
        query = Tweet.update({Tweet.content: content}).where(Tweet.id == tweet_id)
        query.execute()

    @staticmethod
    def delete_tweet(tweet_id):
        query = Tweet.delete().where(Tweet.id == tweet_id)
        query.execute()

    @staticmethod
    def generate_tweet_url(content):
        tweet_url = (
            f"https://twitter.com/intent/tweet?text={urllib.parse.quote(content)}"
        )
        return tweet_url

    @staticmethod
    def display_tweets():
        tweets = TweetManager.get_all_tweets()
        tweet_links = ""
        for tweet_id, content in tweets:
            tweet_url = TweetManager.generate_tweet_url(content)
            tweet_links += f'<p><strong>Tweet ID {tweet_id}:</strong> {content} - <a href="{tweet_url}" target="_blank">Tweet this</a></p>'
        return tweet_links


@agent_action
def post_to_twitter_outbox(content):
    """Post a tweet to the Twitter outbox."""
    TweetManager.add_tweet(content)
    return f"Posted tweet: {content}"


@agent_action
def get_search_term(file_path="search_terms.json"):
    """Return a random search term."""
    try:
        # Read the current list from the file
        with open(file_path, "r") as f:
            search_terms = json.load(f)
    except FileNotFoundError:
        # If the file doesn't exist, initialize with the default list
        search_terms = [
            "SearchGPT AI-powered search engine",
            "Llama 3.1 open-source AI models",
        ]

    if not search_terms:
        raise ValueError("All search terms have been used.")

    # Choose a random term
    term = random.choice(search_terms)

    # Remove the chosen term from the list
    search_terms.remove(term)

    # Write the updated list back to the file
    with open(file_path, "w") as f:
        json.dump(search_terms, f)

    return term
