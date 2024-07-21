import os
from urllib.parse import urljoin, urlparse
import requests
import re
from datetime import datetime
import random

from playground.actions_manager import agent_action
from playground.global_values import GlobalValues


@agent_action
def download_github_readme(repo_url):
    """
    Download the README file from a GitHub repository's default branch.

    This function takes a GitHub repository URL, determines the default branch,
    and attempts to download the README file, trying different common filenames.

    Args:
        repo_url (str): The full URL of the GitHub repository.
            Example: "https://github.com/username/repository"

    Returns:
        str: The content of the README file if successful.
             An error message string if the download fails or the URL is invalid.
    """
    # Extract owner and repo from the URL
    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, repo_url)

    if not match:
        return "Invalid GitHub repository URL"

    owner, repo = match.groups()

    # First, get the default branch using the GitHub API
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        repo_info = response.json()
        default_branch = repo_info["default_branch"]
    except requests.exceptions.RequestException as e:
        return f"Failed to fetch repository information. Error: {str(e)}"

    # List of possible README filenames to try
    readme_filenames = ["README.md", "README.MD", "readme.md", "Readme.md", "ReadMe.md"]

    # Try to download the README using different filename variations
    for filename in readme_filenames:
        readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/{filename}"
        try:
            response = requests.get(readme_url)
            if response.status_code == 200:
                return response.text[:50000]
        except requests.exceptions.RequestException:
            continue

    return "Failed to find a README file in the repository."


@agent_action
def download_readme_and_images(repo_url):
    """
    Download the README file and all images referenced in it from a GitHub repository.

    Args:
        repo_url (str): The full URL of the GitHub repository.
        download_path (str): The local directory path to save the images.

    Returns:
        tuple: A tuple containing the content of the README file and a list of file paths of downloaded images.
    """
    readme_content = download_github_readme(repo_url)
    if "Failed" in readme_content:
        return readme_content, []

    download_path = GlobalValues.ASSISTANTS_WORKING_FOLDER

    # Find all Markdown and HTML image tags
    markdown_image_urls = re.findall(r"!\[.*?\]\((.*?)\)", readme_content)
    html_image_urls = re.findall(r'<img[^>]+src="([^">]+)"', readme_content)
    image_urls = markdown_image_urls + html_image_urls

    downloaded_images = []

    for image_url in image_urls:
        if not image_url.startswith("http"):
            parsed_repo_url = urlparse(repo_url)
            base_url = (
                f"https://raw.githubusercontent.com{parsed_repo_url.path}/master/"
            )
            image_url = urljoin(base_url, image_url)

        try:
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            image_filename = os.path.basename(urlparse(image_url).path)
            local_image_path = os.path.join(download_path, image_filename)
            with open(local_image_path, "wb") as out_file:
                for chunk in response.iter_content(chunk_size=8192):
                    out_file.write(chunk)
            downloaded_images.append(local_image_path)
            # Replace the image URL in the README content with the image filename
            readme_content = readme_content.replace(image_url, image_filename)
        except Exception as e:
            downloaded_images.append(
                f"Error downloading image: {str(e)} please ignore the image."
            )
            readme_content = readme_content.replace(image_url, image_filename)
            continue

    return readme_content, downloaded_images


# # Example usage
# repo_url = "https://github.com/username/repository"
# readme_content = download_github_readme(repo_url)
# print(readme_content)


@agent_action
def get_github_repositories(num_items=10):
    """
    Returns a list of selected repositories.

    Each repository in the list is represented as a dictionary with the following keys:
    - 'name': The name of the repository
    - 'stars': The number of stars the repository has
    - 'url': The URL of the repository on GitHub

    Args:
        num_items (int): The number of random repositories to return. Default is 10.

    Returns:
        list: A list of dictionaries, each representing a repository.
    """
    repositories = [
        {"owner": "StreetLamb", "name": "tribe", "stars": 373},
        {"owner": "OpenBMB", "name": "IoA", "stars": 185},
        {"owner": "PR-Pilot-AI", "name": "pr-pilot", "stars": 93},
        {"owner": "get-salt-AI", "name": "SaltAI_Language_Toolkit", "stars": 80},
        {"owner": "sydverma123", "name": "awesome-ai-repositories", "stars": 52},
        {"owner": "evilsocket", "name": "nerve", "stars": 29},
        {"owner": "hananedupouy", "name": "LLMs-in-Finance", "stars": 27},
        {"owner": "MODSetter", "name": "gpt-instagram", "stars": 25},
        {"owner": "invariantlabs-ai", "name": "invariant", "stars": 23},
        {"owner": "strnad", "name": "CrewAI-Studio", "stars": 14},
        {"owner": "slavakurilyak", "name": "awesome-ai-agents", "stars": 14},
        {"owner": "mongodb-developer", "name": "GenAI-Showcase", "stars": 14},
        {"owner": "microsoft", "name": "call-center-ai", "stars": 13},
        {"owner": "mgilangjanuar", "name": "agentify", "stars": 13},
        {"owner": "tmgthb", "name": "Autonomous-Agents", "stars": 11},
        {"owner": "Jenqyang", "name": "Awesome-AI-Agents", "stars": 10},
        {"owner": "TrafficGuard", "name": "nous", "stars": 10},
        {"owner": "huangjia2019", "name": "ai-agents", "stars": 10},
        {"owner": "EmbeddedLLM", "name": "JamAIBase", "stars": 10},
        {"owner": "JetXu-LLM", "name": "llama-github", "stars": 10},
        {"owner": "npi-ai", "name": "npi", "stars": 9},
        {"owner": "AJaySi", "name": "AI-Writer", "stars": 8},
        {"owner": "Tonyhrule", "name": "Homework-Helper", "stars": 8},
        {"owner": "Yuan-ManX", "name": "ai-game-devtools", "stars": 7},
        {"owner": "reworkd", "name": "bananalyzer", "stars": 7},
        {"owner": "statelyai", "name": "agent", "stars": 7},
        {"owner": "tryAGI", "name": "LangChain", "stars": 7},
        {"owner": "10cl", "name": "chatdev", "stars": 7},
        {
            "owner": "crazyaiproduct",
            "name": "research-opp-cold-email-writer",
            "stars": 7,
        },
        {"owner": "curiousily", "name": "AI-Bootcamp", "stars": 7},
        {"owner": "phodal", "name": "shire", "stars": 6},
        {"owner": "awslabs", "name": "agent-evaluation", "stars": 6},
        {"owner": "sublayerapp", "name": "sublayer", "stars": 6},
        {"owner": "kyrolabs", "name": "awesome-agents", "stars": 6},
        {"owner": "qifan777", "name": "KnowledgeBaseChatSpringAI", "stars": 5},
        {"owner": "rnadigital", "name": "agentcloud", "stars": 5},
        {"owner": "agentsea", "name": "surfkit", "stars": 5},
        {"owner": "agentsea", "name": "agentdesk", "stars": 5},
        {"owner": "Archermmt", "name": "wounderland", "stars": 5},
        {"owner": "Futino", "name": "aitino", "stars": 5},
        {
            "owner": "hanantabak2",
            "name": "AI_Research_Assistant_CrewAI_RAG",
            "stars": 5,
        },
        {"owner": "visendi-labs", "name": "uffe", "stars": 5},
        {"owner": "metauto-ai", "name": "GPTSwarm", "stars": 5},
        {"owner": "happyapplehorse", "name": "agere", "stars": 5},
        {"owner": "Anil-matcha", "name": "AI-Voice-Agent", "stars": 5},
        {"owner": "qrev-ai", "name": "qrev", "stars": 5},
    ]
    num_items = int(num_items)
    selected_repositories = random.sample(repositories, num_items)
    repo_dicts = []

    for repo in selected_repositories:
        owner = repo["owner"]
        name = repo["name"]
        stars = repo["stars"]
        url = f"https://github.com/{owner}/{name}"
        repo_dict = {"name": name, "stars": stars, "url": url}
        repo_dicts.append(repo_dict)

    return repo_dicts


@agent_action
def search_github_repos(search_term, sort_by="stars", order="desc", per_page=30):
    """
    Search for GitHub repositories based on a search term and rank them by stars, forks, and recent usage.

    Parameters:
    search_term (str): The term to search for in GitHub repositories.
    sort_by (str): The criteria to sort the results by. Options are 'stars', 'forks', 'updated'. Default is 'stars'.
    order (str): The order of the results. Options are 'desc' for descending and 'asc' for ascending. Default is 'desc'.
    per_page (int): The number of results per page. Maximum is 100. Default is 30.

    Returns:
    None: Prints the repository details including name, stars, forks, last updated date, and URL.
    """
    base_url = "https://api.github.com/search/repositories"

    # Set the parameters for the search query
    params = {"q": search_term, "sort": sort_by, "order": order, "per_page": per_page}

    # Make the request to the GitHub API
    response = requests.get(base_url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        repos = response.json()["items"]

        repo_details = []
        for repo in repos:
            name = repo["name"]
            stars = repo["stargazers_count"]
            forks = repo["forks_count"]
            updated_at = repo["updated_at"]
            url = repo["html_url"]
            last_updated = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")

            # Create a dictionary object for each repository
            repo_dict = {
                "name": name,
                "stars": stars,
                "forks": forks,
                "last_updated": last_updated,
                "url": url,
            }

            # Add the repository details to the list
            repo_details.append(repo_dict)

        # Return the list of repository details
        return repo_details
    else:
        print(f"Failed to retrieve repositories: {response.status_code}")
        print(response.json())


# # Usage example
# search_term = "machine learning"
# search_github_repos(search_term)
