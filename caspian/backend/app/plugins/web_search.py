import requests
from typing import Optional
import json
from time import sleep

def search_with_retry(query: str, max_retries: int = 3) -> Optional[dict]:
    """
    Perform a web search with retries and error handling.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&no_html=1"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                return None
            sleep(1)  # Wait before retrying
    return None

def register(query: str) -> str:
    """
    Perform a web search using DuckDuckGo Instant Answer API and return a summary.
    Includes improved error handling and fallback mechanisms.
    """
    try:
        data = search_with_retry(query)
        if not data:
            return "I apologize, but I'm having trouble accessing web search at the moment. Please try again in a moment."

        # Try different response fields in order of relevance
        if data.get("AbstractText"):
            return data["AbstractText"]
        
        if data.get("Answer"):
            return data["Answer"]
            
        if data.get("RelatedTopics"):
            topics = data["RelatedTopics"]
            relevant_topics = []
            
            for topic in topics:
                if isinstance(topic, dict):
                    if "Text" in topic:
                        relevant_topics.append(topic["Text"])
                    elif "Result" in topic:
                        relevant_topics.append(topic["Result"])
                        
            if relevant_topics:
                return relevant_topics[0]  # Return the most relevant topic
                
        return "I found some information, but it may not be directly relevant to your query. Could you try rephrasing your question?"
        
    except Exception as e:
        return f"I encountered an error while searching: {str(e)}. Please try again with a different query."
