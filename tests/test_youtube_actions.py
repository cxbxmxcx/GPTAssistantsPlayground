from playground.assistant_actions.youtube_search import search_youtube_videos


def test_youtube_search():
    videos = search_youtube_videos("GPT Agents")

    assert len(videos) > 0
