import os
from googleapiclient.discovery import build
from typing import Dict, List, Optional

class SearchTool:
    """Tool for performing web searches using Google Custom Search API"""
    
    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        """Initialize search tool with API key and search engine ID
        
        Args:
            api_key (str, optional): Google API key. Defaults to env var GOOGLE_API_KEY.
            search_engine_id (str, optional): Google Custom Search Engine ID. Defaults to env var GOOGLE_SEARCH_ENGINE_ID.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        print(f"Debug - API Key: {self.api_key[:10]}...")  # Print first 10 chars of API key
        print(f"Debug - Search Engine ID: {self.search_engine_id}")
        
        if not self.api_key:
            raise ValueError("Google API key not found. Set GOOGLE_API_KEY env var.")
        if not self.search_engine_id:
            raise ValueError("Google Search Engine ID not found. Set GOOGLE_SEARCH_ENGINE_ID env var.")
            
        # Initialize the Custom Search API service
        self.service = build("customsearch", "v1", developerKey=self.api_key)
            
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Perform Google search via Custom Search API
        
        Args:
            query (str): Search query
            num_results (int, optional): Number of results to return. Defaults to 5.
            
        Returns:
            List[Dict]: Search results with title, snippet, and link
        """
        try:
            print(f"Debug - Executing search with query: {query}")
            # Execute search
            result = self.service.cse().list(
                q=query,
                cx=self.search_engine_id,
                num=num_results
            ).execute()
            
            print(f"Debug - API Response: {result}")
            
            # Extract search results
            if "items" not in result:
                return []
                
            processed_results = []
            for item in result["items"]:
                processed_results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", "")
                })
                
            return processed_results
            
        except Exception as e:
            print(f"Error performing search: {str(e)}")
            print(f"Debug - Full error details: {e.__dict__}")
            return []
