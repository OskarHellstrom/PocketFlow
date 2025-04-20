from pocketflow import Node, AsyncNode
from tools.search import SearchTool
from tools.web_search import WebSearchTool
from tools.parser import analyze_results
from utils.call_llm import call_llm
from typing import List, Dict
import yaml
import os

class DecideSearchType(Node):
    """Node to decide between Google and Web search based on query"""
    
    def prep(self, shared):
        self.shared = shared  # Store shared data
        return shared.get("query"), shared.get("context", "")
        
    def exec(self, inputs):
        query, context = inputs
        
        print(f"🤔 Deciding search type for query: {query}")
        
        prompt = f"""Analyze this search query and decide whether to use Google Search or Web Search:

Query: {query}
Previous Context: {context}

Consider:
- Google Search is better for:
  * Specific, factual queries
  * Recent information
  * Well-known topics
  * Structured data
  
- Web Search is better for:
  * Exploratory research
  * Less common topics
  * Multiple perspectives
  * Unstructured information

Return your decision in YAML format without any backticks or yaml tags:
search_type: google OR web
reason: <why you chose this search type>
search_query: <refined search query>
"""
        try:
            response = call_llm(prompt)
            print("LLM Response:", response)
            
            # Clean up response - remove any backticks and yaml tags
            yaml_str = response.replace('```yaml', '').replace('```', '').strip()
            
            try:
                decision = yaml.safe_load(yaml_str)
                if not isinstance(decision, dict):
                    raise ValueError("Response not in expected format")
                
                # Store the decision in shared data
                self.shared["search_type"] = decision.get("search_type", "google")
                self.shared["search_query"] = decision.get("search_query", query)
                
                print(f"🔍 Decided to use {decision.get('search_type', 'google').upper()} search")
                return decision.get("search_type", "google")
                
            except Exception as e:
                print(f"Error parsing YAML response: {str(e)}")
                # Default to google search on error
                self.shared["search_type"] = "google"
                self.shared["search_query"] = query
                print("🔍 Defaulting to GOOGLE search due to error")
                return "google"
                
        except Exception as e:
            print(f"Error calling LLM: {str(e)}")
            # Default to google search on error
            self.shared["search_type"] = "google"
            self.shared["search_query"] = query
            print("🔍 Defaulting to GOOGLE search due to error")
            return "google"
        
    def post(self, shared, prep_res, exec_res):
        return exec_res

class GoogleSearchNode(Node):
    """Node to perform Google search"""
    
    def prep(self, shared):
        return shared.get("search_query"), shared.get("num_results", 5)
        
    def exec(self, inputs):
        query, num_results = inputs
        if not query:
            return []
            
        # Print debug info about environment variables
        print(f"Debug - GOOGLE_API_KEY exists: {bool(os.getenv('GOOGLE_API_KEY'))}")
        print(f"Debug - GOOGLE_SEARCH_ENGINE_ID exists: {bool(os.getenv('GOOGLE_SEARCH_ENGINE_ID'))}")
            
        searcher = SearchTool()
        return searcher.search(query, num_results)
        
    def post(self, shared, prep_res, exec_res):
        shared["search_results"] = exec_res
        return "default"

class WebSearchNode(Node):
    """Node to perform web search"""
    
    def prep(self, shared):
        return shared.get("search_query"), shared.get("num_results", 5)
        
    def exec(self, inputs):
        query, num_results = inputs
        if not query:
            return []
            
        print(f"\n🔍 Executing web search with query: {query}")
        print(f"Number of results requested: {num_results}")
        
        searcher = WebSearchTool()
        results = searcher.search(query, num_results)
        
        print("\n📊 Web Search Results:")
        for i, result in enumerate(results, 1):
            print(f"\n[Result {i}]")
            print(f"Title: {result.get('title', 'N/A')}")
            print(f"URL: {result.get('link', 'N/A')}")
            print(f"Snippet: {result.get('snippet', 'N/A')[:200]}...")
            
        return results
        
    def post(self, shared, prep_res, exec_res):
        shared["search_results"] = exec_res
        return "default"

class AnalyzeResultsNode(Node):
    """Node to analyze search results and decide next action"""
    
    def __init__(self):
        super().__init__()
        self.max_attempts_per_approach = 3
        self.min_confidence_threshold = 0.3

    def prep(self, shared):
        self.shared = shared  # Store shared data
        return {
            'search_results': shared.get('search_results', []),
            'query': shared.get('query', ''),
            'search_attempts': shared.get('search_attempts', 0),
            'previous_queries': shared.get('previous_queries', []),
            'found_information': shared.get('found_information', {}),
            'search_types_tried': shared.get('search_types_tried', set()),
            'current_search_type': shared.get('search_type', 'google')
        }

    def exec(self, params):
        print("\nSearch Analysis:")
        
        search_results = params.get('search_results', [])
        query = params.get('query', '')
        search_attempts = params.get('search_attempts', 0)
        previous_queries = params.get('previous_queries', [])
        found_information = params.get('found_information', {})
        search_types_tried = params.get('search_types_tried', set())
        current_search_type = params.get('current_search_type', 'google')
        
        # Track search type and query
        search_types_tried.add(current_search_type)
        if query not in previous_queries:
            previous_queries.append(query)

        analysis_prompt = f"""Analyze these search results and determine next steps.

Query: {query}
Search Attempts: {search_attempts}
Previous Queries Tried: {previous_queries}
Search Types Tried: {list(search_types_tried)}
Information Found So Far: {found_information}

Consider:
1. Have we found new relevant information not already in our found_information?
2. Are we getting similar results to previous searches?
3. If stuck (similar results, no new info), consider:
   - Trying a different search type (google/web) if not tried
   - Broadening the search to find context
   - Breaking down the query into smaller parts
   - Looking for related but different information
4. Only give up and return final answer if:
   - We've tried both search types AND
   - Multiple query variations yielded no new info AND
   - We have sufficient confidence in our findings OR
   - Further searching is unlikely to help

Confidence Scoring Guidelines:
- 0.0: No relevant information found
- 0.3: Some related but indirect information found
- 0.5: Partial answer found but significant gaps remain
- 0.7: Most of the query answered but some details missing
- 1.0: Complete and verified answer found


Format your response in YAML without backticks or tags:
summary: <one sentence summary of new findings>
confidence: <float 0.0-1.0 following guidelines above>
action: <search/answer>
reason: <one sentence explanation>
suggested_search_type: <google/web - only if action is search>
key_points:
  - <point 1>
  - <point 2>
found_information:
  <key>: <value>
next_query: <query if action is search>
"""

        try:
            response = call_llm(analysis_prompt + "\n\nResults to analyze:\n" + str(search_results))
            print(response)
            
            # Clean up response - remove any backticks and yaml tags
            yaml_str = response.replace('```yaml', '').replace('```', '').strip()
            
            try:
                analysis = yaml.safe_load(yaml_str)
                if not isinstance(analysis, dict):
                    raise ValueError("Response not in expected format")
                
                # Update found information with any new information
                if 'found_information' in analysis:
                    found_information.update(analysis['found_information'])
                
                # Update shared data
                self.shared['previous_queries'] = previous_queries
                self.shared['found_information'] = found_information
                self.shared['search_types_tried'] = search_types_tried
                
                # Validate and adjust confidence
                confidence = float(analysis.get('confidence', 0))
                if not found_information and confidence > 0:
                    # If no information found, confidence must be 0
                    confidence = 0.0
                    analysis['confidence'] = 0.0
                    analysis['reason'] = 'No relevant information found, confidence adjusted to 0.0'
                
                # Determine if we should continue searching
                all_types_tried = len(search_types_tried) >= 2
                many_attempts = search_attempts >= self.max_attempts_per_approach * 2
                
                # Force an answer if:
                # 1. We've tried all search types and have good confidence, or
                # 2. We've tried many times with no success
                if (all_types_tried and confidence >= self.min_confidence_threshold) or \
                   (many_attempts and confidence < self.min_confidence_threshold):
                    analysis['action'] = 'answer'
                    if confidence < self.min_confidence_threshold:
                        analysis['reason'] = 'Exhausted search options without finding sufficient information'
                    else:
                        analysis['reason'] = 'Found sufficient information to answer query'
                elif analysis['action'] == 'search':
                    # If continuing to search, update search type
                    suggested_type = analysis.get('suggested_search_type')
                    if suggested_type and suggested_type not in search_types_tried:
                        self.shared['search_type'] = suggested_type
                
                return analysis
                
            except Exception as e:
                print(f"Error parsing YAML response: {str(e)}")
                return self._handle_error('Failed to parse analysis results', str(e), found_information)
                
        except Exception as e:
            print(f"Error calling LLM: {str(e)}")
            return self._handle_error('Failed to analyze results', str(e), found_information)

    def _handle_error(self, summary, error, found_information):
        """Handle errors in analysis by suggesting to try alternative search approach"""
        return {
            'summary': summary,
            'confidence': 0.0,
            'action': 'search',  # Try another search instead of giving up
            'reason': f'Error occurred: {error}. Attempting alternative search approach.',
            'suggested_search_type': 'web' if self.shared.get('search_type') == 'google' else 'google',
            'key_points': [],
            'found_information': found_information,
            'next_query': self.shared.get('query')  # Retry with same query but different approach
        }

    def post(self, shared, params, exec_res):
        print(f"\nSummary: {exec_res.get('summary', 'No summary available')}")
        print(f"Confidence: {exec_res.get('confidence', 0.0):.2f}")
        print(f"Action: {exec_res.get('action', 'search')}")
        print(f"Reason: {exec_res.get('reason', 'No reason provided')}")
        
        if exec_res.get('key_points'):
            print("\nKey Points:")
            for point in exec_res['key_points']:
                print(f"- {point}")
        
        if exec_res.get('found_information'):
            print("\nAccumulated Information:")
            for key, value in exec_res['found_information'].items():
                print(f"- {key}: {value}")
                
        if exec_res.get('action') == 'search' and exec_res.get('next_query'):
            print(f"\nNext Search Query: {exec_res['next_query']}")
            
        return exec_res.get('action', 'search')

class AnswerQuestionNode(Node):
    """Node to provide final answer"""
    
    def prep(self, shared):
        return shared.get("query"), shared.get("found_information", {}), shared.get("search_results", [])

    def exec(self, inputs):
        query, found_info, search_results = inputs
        
        # Extract source links from search results
        sources = []
        for result in search_results:
            if 'link' in result and 'title' in result:
                sources.append({
                    'title': result['title'],
                    'url': result['link']
                })

        # Format answer based on accumulated information
        if found_info:
            answer = "Based on the available information:\n"
            for key, value in found_info.items():
                if value:  # Only include non-empty values
                    answer += f"- {key}: {value}\n"
        else:
            answer = "No relevant information was found for your query."

        return {
            "answer": answer.strip(),
            "sources": sources
        }
        
    def post(self, shared, prep_res, exec_res):
        shared["final_answer"] = exec_res
        
        print("\nFinal Answer:")
        print(exec_res["answer"])
        if exec_res["sources"]:
            print("\nSources:")
            for source in exec_res["sources"]:
                print(f"- {source['title']}: {source['url']}")
        
        return "default"

class AnswerReviewNode(Node):
    """Node to allow human review of final answer"""
    
    def prep(self, shared):
        self.shared = shared  # Store shared data
        answer = shared.get("final_answer", {})
        return answer
        
    def exec(self, inputs):
        answer = inputs
        
        print("\n=== Answer Review ===")
        print("\nAnswer:")
        print(answer.get("answer", "N/A"))
        
        print("\nSources:")
        if 'source_links' in answer:
            for source in answer['source_links']:
                print(f"- {source['title']}: {source['url']}")
        else:
            print("No sources available")
        
        print("\nOptions:")
        print("1. Approve answer")
        print("2. Modify answer")
        
        choice = input("\nEnter your choice (1-2): ")
        
        if choice == "1":
            return "approved"
        elif choice == "2":
            new_answer = input("Enter modified answer: ")
            answer["answer"] = new_answer
            self.shared["final_answer"] = answer
            return "modified"
        else:
            return "approved"  # Default to approved if invalid choice
        
    def post(self, shared, prep_res, exec_res):
        return "default"

def calculate_confidence(self, found_info, search_results, query_type):
    base_confidence = 0.0
    
    # Weight by source reliability
    source_scores = [self.rate_source_reliability(result) for result in search_results]
    
    # Weight by information completeness
    completeness = self.assess_completeness(found_info, query_type)
    
    # Weight by cross-validation
    validation_score = self.check_cross_validation(found_info)
    
    # Combine scores
    confidence = (
        0.4 * completeness +
        0.3 * max(source_scores, default=0) +
        0.3 * validation_score
    )
    
    return min(1.0, confidence)
