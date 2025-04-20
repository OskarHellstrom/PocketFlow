from pocketflow import Flow, Node
from nodes import (
    DecideSearchType,
    GoogleSearchNode,
    WebSearchNode,
    AnalyzeResultsNode,
    AnswerQuestionNode,
    AnswerReviewNode
)

def create_flow():
    # Create nodes
    decide = DecideSearchType()
    google = GoogleSearchNode()
    web = WebSearchNode()
    analyze = AnalyzeResultsNode()
    answer = AnswerQuestionNode()
    answer_review = AnswerReviewNode()

    # Connect nodes
    decide - "google" >> google
    decide - "web" >> web
    google - "default" >> analyze
    web - "default" >> analyze
    analyze - "search" >> decide
    analyze - "answer" >> answer
    answer - "default" >> answer_review

    # Create and return flow starting with decide node
    return Flow(start=decide)

if __name__ == "__main__":
    flow = create_flow()
    
    # Initialize shared data
    shared = {}
    shared["query"] = input("Enter your search query: ")
    shared["search_attempts"] = 0
    shared["search_types_tried"] = set()
    shared["previous_queries"] = []
    shared["found_information"] = {}
    
    # Run flow with improved search strategy
    while True:
        result = flow.run(shared)
        shared["search_attempts"] += 1
        
        # Break if we've reached a final answer
        if result == "default":
            break
        
        # Break if we've tried too many times without success
        if shared["search_attempts"] >= 10:  # Absolute maximum attempts
            print("\nReached maximum number of search attempts. Stopping search.")
            break
