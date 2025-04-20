import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time

class WebSearchTool:
    """Tool for performing web searches using direct web scraping"""
    
    def __init__(self):
        """Initialize web search tool with necessary headers"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Perform web search using DuckDuckGo
        
        Args:
            query (str): Search query
            num_results (int, optional): Number of results to return. Defaults to 5.
            
        Returns:
            List[Dict]: Search results with title, snippet, and link
        """
        try:
            # Use DuckDuckGo as the search engine
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            
            # Make the request
            response = requests.get(search_url, headers=self.headers)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract results
            results = []
            for result in soup.find_all('div', class_='result'):
                if len(results) >= num_results:
                    break
                    
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem and snippet_elem:
                    results.append({
                        'title': title_elem.text.strip(),
                        'snippet': snippet_elem.text.strip(),
                        'link': title_elem['href']
                    })
                    
                # Be nice to the server
                time.sleep(1)
                
            return results
            
        except Exception as e:
            print(f"Error performing web search: {str(e)}")
            return [] 