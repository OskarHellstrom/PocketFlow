from flow import create_search_flow

def main():
    print("Welcome to the Search Flow!")
    print("Enter your query (or 'quit' to exit):")
    
    while True:
        query = input("\nQuery: ").strip()
        if query.lower() == 'quit':
            break
            
        if not query:
            print("Please enter a valid query.")
            continue
            
        print("\nProcessing your query...")
        flow = create_search_flow()
        flow.run({'query': query})
        
        print("\nWould you like to search again? (yes/no)")
        if input().lower() != 'yes':
            break
            
    print("\nThank you for using the Search Flow!")

if __name__ == "__main__":
    main() 