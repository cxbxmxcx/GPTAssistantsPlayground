import random
import urllib.parse
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
def get_search_term():
    """Return a random search term."""
    search_terms = [
        "AI Agents",
        # "OpenAI",
        # "AI Music",
        # "AI Video",
        # "AI Startups",
        # "AI in Software Development",
    ]
    top_search_terms = [
        "Overwatch",
        "Nintendo",
        "Xbox",
        "NASA",
        "Blizzard Entertainment",
        "Artificial Intelligence",
        "Phys.org",
        "GamesIndustry.biz",
        "Symmetra",
        "Mars 2020",
    ]
    return random.choice(search_terms)
