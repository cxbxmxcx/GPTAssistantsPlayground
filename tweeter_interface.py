import gradio as gr
import urllib.parse
from peewee import SqliteDatabase, Model, IntegerField, TextField

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


# Define Gradio app
def get_tweet_options():
    tweets = TweetManager.get_all_tweets()
    options = [("Create a new Tweet", "new")]
    options.extend(
        [(f"{tweet_id}: {content}", str(tweet_id)) for tweet_id, content in tweets]
    )
    return options


def handle_selection(selection):
    if selection == "new":
        return gr.update(visible=True), gr.update(visible=False), "", ""
    else:
        tweet_id = int(selection)
        tweet_content = Tweet.get(Tweet.id == tweet_id).content
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            tweet_content,
            tweet_id,
        )


def handle_add_tweet(content):
    TweetManager.add_tweet(content)
    return (
        gr.update(choices=get_tweet_options()),
        "",
        gr.update(visible=False),
        gr.update(visible=False),
        TweetManager.display_tweets(),
    )


def handle_update_tweet(tweet_id, content):
    TweetManager.update_tweet(tweet_id, content)
    return (
        gr.update(choices=get_tweet_options()),
        "",
        gr.update(visible=False),
        gr.update(visible=False),
        TweetManager.display_tweets(),
    )


def handle_delete_tweet(tweet_id):
    TweetManager.delete_tweet(tweet_id)
    return (
        gr.update(choices=get_tweet_options()),
        "",
        gr.update(visible=False),
        gr.update(visible=False),
        TweetManager.display_tweets(),
    )


with gr.Blocks() as demo:
    gr.Markdown("## Manage Tweets")

    tweet_selector = gr.Dropdown(
        label="Select Tweet", choices=get_tweet_options(), value=None
    )
    create_tweet_panel = gr.Group(visible=False)
    update_tweet_panel = gr.Group(visible=False)

    with create_tweet_panel:
        gr.Markdown("### Create a New Tweet")
        new_tweet_input = gr.Textbox(label="Tweet Content")
        add_tweet_button = gr.Button("Add Tweet")

    with update_tweet_panel:
        gr.Markdown("### Update/Delete Tweet")
        update_tweet_input = gr.Textbox(label="Tweet Content")
        update_tweet_id = gr.Number(label="Tweet ID", visible=False)
        update_tweet_button = gr.Button("Update Tweet")
        delete_tweet_button = gr.Button("Delete Tweet")

    tweet_display_output = gr.HTML()

    tweet_selector.change(
        handle_selection,
        inputs=tweet_selector,
        outputs=[
            create_tweet_panel,
            update_tweet_panel,
            update_tweet_input,
            update_tweet_id,
        ],
    )
    add_tweet_button.click(
        handle_add_tweet,
        inputs=new_tweet_input,
        outputs=[
            tweet_selector,
            new_tweet_input,
            create_tweet_panel,
            update_tweet_panel,
            tweet_display_output,
        ],
    )
    update_tweet_button.click(
        handle_update_tweet,
        inputs=[update_tweet_id, update_tweet_input],
        outputs=[
            tweet_selector,
            update_tweet_input,
            create_tweet_panel,
            update_tweet_panel,
            tweet_display_output,
        ],
    )
    delete_tweet_button.click(
        handle_delete_tweet,
        inputs=update_tweet_id,
        outputs=[
            tweet_selector,
            update_tweet_input,
            create_tweet_panel,
            update_tweet_panel,
            tweet_display_output,
        ],
    )

    demo.load(
        lambda: (get_tweet_options(), TweetManager.display_tweets()),
        outputs=[tweet_selector, tweet_display_output],
    )


demo.launch(inbrowser=True, share=True)
