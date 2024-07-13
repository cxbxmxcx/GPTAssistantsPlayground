import requests
import re
from datetime import datetime

from playground.actions_manager import agent_action


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

    Raises:
        requests.exceptions.RequestException: If there's an error making the HTTP request.

    Examples:
        >>> repo_url = "https://github.com/username/repository"
        >>> readme_content = download_github_readme(repo_url)
        >>> print(readme_content[:100])  # Print first 100 characters of README
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
                return response.text
        except requests.exceptions.RequestException:
            continue

    return "Failed to find a README file in the repository."


# Example usage
repo_url = "https://github.com/username/repository"
readme_content = download_github_readme(repo_url)
print(readme_content)


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
