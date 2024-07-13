import gradio as gr
import urllib.parse
from peewee import SqliteDatabase, Model, CharField, TextField
import uuid

# Initialize Peewee database
db = SqliteDatabase("reddit.db")


class RedditPost(Model):
    id = CharField(primary_key=True, default=lambda: str(uuid.uuid4()))
    title = TextField()
    content = TextField()
    subreddit = CharField()

    class Meta:
        database = db


db.connect()
db.create_tables([RedditPost])


class RedditPostManager:
    @staticmethod
    def get_all_posts():
        posts = RedditPost.select()
        return [(post.id, post.title, post.subreddit) for post in posts]

    @staticmethod
    def add_post(title, content, subreddit):
        RedditPost.create(title=title, content=content, subreddit=subreddit)

    @staticmethod
    def update_post(post_id, title, content, subreddit):
        update_data = {
            RedditPost.title: title,
            RedditPost.content: content,
            RedditPost.subreddit: subreddit,
        }

        query = RedditPost.update(update_data).where(RedditPost.id == post_id)
        query.execute()

    @staticmethod
    def delete_post(post_id):
        query = RedditPost.delete().where(RedditPost.id == post_id)
        query.execute()

    # https://www.reddit.com/r/GPTAgents/submit/?url=https%3A%2F%2Fyoutube.com%2Fwatch%3Fv%3DBftm2UxEgfw%26si%3Dlet9P-i4i43np-xw&title=Building+Autonomous+Agents&type=TEXT&text=This+is+an+example+post+for+the+GPT+Agents+subreddit
    @staticmethod
    def generate_reddit_url(title, subreddit, content):
        reddit_url = f"https://www.reddit.com/r/{subreddit}/submit?selftext=true&title={urllib.parse.quote(title)}&text={urllib.parse.quote(content)}"
        return reddit_url

    @staticmethod
    def display_posts():
        posts = RedditPostManager.get_all_posts()
        post_links = ""
        for post_id, title, subreddit in posts:
            post = RedditPost.get(RedditPost.id == post_id)
            reddit_url = RedditPostManager.generate_reddit_url(
                title, subreddit, post.content
            )
            post_links += f'<p><strong>Post ID {post_id}:</strong> {title} (r/{subreddit}) - <a href="{reddit_url}" target="_blank">Post to Reddit</a></p>'
        return post_links


# Define Gradio app
def get_post_options():
    posts = RedditPostManager.get_all_posts()
    options = [("Create a new Post", "new")]
    options.extend(
        [
            (f"{post_id}: {title} (r/{subreddit})", post_id)
            for post_id, title, subreddit in posts
        ]
    )
    return options


def handle_selection(selection):
    if selection == "new":
        return gr.update(visible=True), gr.update(visible=False), "", "", "", ""
    else:
        post = RedditPost.get(RedditPost.id == selection)
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            post.title,
            post.content,
            post.subreddit,
            post.id,
        )


def handle_add_post(title, content, subreddit):
    RedditPostManager.add_post(title, content, subreddit)
    return (
        gr.update(choices=get_post_options()),
        "",
        "",
        "",
        gr.update(visible=False),
        gr.update(visible=False),
        RedditPostManager.display_posts(),
    )


def handle_update_post(post_id, title, content, subreddit):
    RedditPostManager.update_post(post_id, title, content, subreddit)
    return (
        gr.update(choices=get_post_options()),
        "",
        "",
        "",
        gr.update(visible=False),
        gr.update(visible=False),
        RedditPostManager.display_posts(),
    )


def handle_delete_post(post_id):
    RedditPostManager.delete_post(post_id)
    return (
        gr.update(choices=get_post_options()),
        "",
        "",
        "",
        gr.update(visible=False),
        gr.update(visible=False),
        RedditPostManager.display_posts(),
    )


with gr.Blocks() as demo:
    gr.Markdown("## Manage Reddit Posts")

    post_selector = gr.Dropdown(
        label="Select Post", choices=get_post_options(), value=None
    )
    create_post_panel = gr.Group(visible=False)
    update_post_panel = gr.Group(visible=False)

    with create_post_panel:
        gr.Markdown("### Create a New Reddit Post")
        new_title_input = gr.Textbox(label="Post Title")
        new_content_input = gr.Textbox(label="Post Content")
        new_subreddit_input = gr.Textbox(label="Subreddit")
        add_post_button = gr.Button("Add Post")

    with update_post_panel:
        gr.Markdown("### Update/Delete Reddit Post")
        update_title_input = gr.Textbox(label="Post Title")
        update_content_input = gr.Textbox(label="Post Content")
        update_subreddit_input = gr.Textbox(label="Subreddit")
        update_post_id = gr.Textbox(label="Post ID", visible=False)
        update_post_button = gr.Button("Update Post")
        delete_post_button = gr.Button("Delete Post")

    post_display_output = gr.HTML()

    post_selector.change(
        handle_selection,
        inputs=post_selector,
        outputs=[
            create_post_panel,
            update_post_panel,
            update_title_input,
            update_content_input,
            update_subreddit_input,
            update_post_id,
        ],
    )
    add_post_button.click(
        handle_add_post,
        inputs=[new_title_input, new_content_input, new_subreddit_input],
        outputs=[
            post_selector,
            new_title_input,
            new_content_input,
            new_subreddit_input,
            create_post_panel,
            update_post_panel,
            post_display_output,
        ],
    )
    update_post_button.click(
        handle_update_post,
        inputs=[
            update_post_id,
            update_title_input,
            update_content_input,
            update_subreddit_input,
        ],
        outputs=[
            post_selector,
            update_title_input,
            update_content_input,
            update_subreddit_input,
            create_post_panel,
            update_post_panel,
            post_display_output,
        ],
    )
    delete_post_button.click(
        handle_delete_post,
        inputs=update_post_id,
        outputs=[
            post_selector,
            update_title_input,
            update_content_input,
            update_subreddit_input,
            create_post_panel,
            update_post_panel,
            post_display_output,
        ],
    )

    demo.load(
        lambda: (get_post_options(), RedditPostManager.display_posts()),
        outputs=[post_selector, post_display_output],
    )

demo.launch(inbrowser=True, share=True)
