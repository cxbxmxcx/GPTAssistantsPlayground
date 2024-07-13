import json
import urllib.parse

import requests
from youtube_transcript_api import YouTubeTranscriptApi

from playground.actions_manager import agent_action


class YoutubeSearch:
    def __init__(self, search_terms: str, max_results=None, publish_time="today"):
        self.search_terms = search_terms
        self.max_results = int(max_results)
        self.filter = self._get_filter(publish_time)
        self.videos = self._search()

        # Upload Date:
        # EgQIAhAB: Today
        # EgQIAxAB: This week
        # EgQIBBAB: This month
        # EgQIBRAB: This year

    def _get_filter(self, publish_time):
        if publish_time == "today":
            return "EgQIAhAB"
        elif publish_time == "this week":
            return "EgQIAxAB"
        elif publish_time == "this month":
            return "EgQIBBAB"
        elif publish_time == "this year":
            return "EgQIBRAB"
        else:
            return "EgQIAhAB"

    def _search(self):
        encoded_search = urllib.parse.quote_plus(self.search_terms)
        BASE_URL = "https://youtube.com"
        # This filter shows only videos uploaded in the last hour, sorted by relevance
        url = f"{BASE_URL}/results?search_query={encoded_search}&sp={self.filter}"
        response = requests.get(url).text
        while "ytInitialData" not in response:
            response = requests.get(url).text
        results = self._parse_html(response)
        if self.max_results is not None and len(results) > self.max_results:
            return results[: self.max_results]
        return results

    def _parse_html(self, response):
        results = []
        start = response.index("ytInitialData") + len("ytInitialData") + 3
        end = response.index("};", start) + 1
        json_str = response[start:end]
        data = json.loads(json_str)

        for contents in data["contents"]["twoColumnSearchResultsRenderer"][
            "primaryContents"
        ]["sectionListRenderer"]["contents"]:
            for video in contents["itemSectionRenderer"]["contents"]:
                res = {}
                if "videoRenderer" in video.keys():
                    video_data = video.get("videoRenderer", {})
                    res["id"] = video_data.get("videoId", None)
                    res["thumbnails"] = [
                        thumb.get("url", None)
                        for thumb in video_data.get("thumbnail", {}).get(
                            "thumbnails", [{}]
                        )
                    ]
                    res["title"] = (
                        video_data.get("title", {})
                        .get("runs", [[{}]])[0]
                        .get("text", None)
                    )
                    res["long_desc"] = (
                        video_data.get("descriptionSnippet", {})
                        .get("runs", [{}])[0]
                        .get("text", None)
                    )
                    res["channel"] = (
                        video_data.get("longBylineText", {})
                        .get("runs", [[{}]])[0]
                        .get("text", None)
                    )
                    res["duration"] = video_data.get("lengthText", {}).get(
                        "simpleText", 0
                    )
                    res["views"] = video_data.get("viewCountText", {}).get(
                        "simpleText", 0
                    )
                    res["publish_time"] = video_data.get("publishedTimeText", {}).get(
                        "simpleText", 0
                    )
                    res["url_suffix"] = (
                        video_data.get("navigationEndpoint", {})
                        .get("commandMetadata", {})
                        .get("webCommandMetadata", {})
                        .get("url", None)
                    )
                    results.append(res)

            if results:
                return results
        return results

    def to_dict(self, clear_cache=True):
        result = self.videos
        if clear_cache:
            self.videos = ""
        return result

    def to_json(self, clear_cache=True):
        result = json.dumps({"videos": self.videos})
        if clear_cache:
            self.videos = ""
        return result


@agent_action
def search_youtube_videos(query: str, max_results=5, publish_time="this year"):
    """
    Search for YouTube videos based on a query and filter by publish time.

    This function uses the YouTube Search API to find videos matching the specified query.
    The results can be limited by the maximum number of results and filtered by the
    publish time (e.g., today, this week, this month, this year).

    Args:
        query (str): The search query string.
        max_results (int, optional): The maximum number of search results to return. Default is 5.
        publish_time (str, optional): The time filter for the search results. Options include "today",
                                      "this week", "this month", and "this year". Default is "today".

    Returns:
        list: A list of dictionaries containing video titles and their corresponding IDs.
    """
    results = YoutubeSearch(query, max_results=3, publish_time=publish_time)
    videos = results.videos
    return [{"title": video["title"], "id": video["id"]} for video in videos]


search_cache = []


@agent_action
def search_new_youtube_videos(query: str, max_results=10):
    """Searches for new videos on YouTube based on the query string and returns the video titles and IDs."""
    global search_cache
    results = YoutubeSearch(query, max_results=max_results)
    videos = results.videos
    new_videos = [
        {"title": video["title"], "id": video["id"]}
        for video in videos
        if video["id"] not in search_cache
    ]
    search_cache += [video["id"] for video in videos]
    return new_videos


@agent_action
def download_transcripts(video_ids):
    """Downloads the transcripts for the given video IDs."""
    if isinstance(video_ids, str):
        video_ids = [video_ids]
    transcripts = {}
    for video_id in video_ids:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join(
                [segment["text"].replace("\xa0", " ") for segment in transcript]
            )
            transcripts[video_id] = transcript_text
        except Exception as e:
            transcripts[video_id] = f"Error retrieving transcript: {str(e)}"
    return transcripts
