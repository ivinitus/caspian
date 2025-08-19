import requests

def register(query: str) -> str:
    """
    Perform a web search using DuckDuckGo Instant Answer API and return a summary.
    """
    url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&no_html=1"
    resp = requests.get(url)
    if resp.status_code != 200:
        return "Sorry, I couldn't fetch search results."
    data = resp.json()
    # Prefer AbstractText, fallback to related topics or say not found
    if data.get("AbstractText"):
        return data["AbstractText"]
    elif data.get("RelatedTopics"):
        topics = data["RelatedTopics"]
        if topics and isinstance(topics, list) and "Text" in topics[0]:
            return topics[0]["Text"]
    return "No relevant results found."
