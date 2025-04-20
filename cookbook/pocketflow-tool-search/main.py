from flow import create_search_flow
import asyncio

async def main():
    # Create the flow
    flow = create_search_flow()
    
    # Get user input
    query = input("Enter your search query: ")
    context = input("Enter any context (optional): ")
    
    # Initialize shared data
    shared = {
        "query": query,
        "context": context,
        "search_type": None,
        "search_query": None,
        "search_results": None,
        "analysis": None,
        "final_answer": None
    }
    
    # Run the flow
    try:
        await flow.run_async(shared)
        print("\n=== Final Answer ===")
        print(shared.get("final_answer", {}).get("answer", "No answer generated"))
    except Exception as e:
        print(f"Error running flow: {e}")

if __name__ == "__main__":
    asyncio.run(main())
