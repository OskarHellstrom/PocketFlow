import os
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of utils directory)
ROOT_DIR = Path(__file__).parent.parent

# Load environment variables
load_dotenv()

# Debug: Print API key before configuring
api_key = os.getenv("GOOGLE_API_KEY")
print(f"Debug - API Key before configure: {api_key[:10]}..." if api_key else "No API key found")

if api_key:
    genai.configure(api_key=api_key)
    print("Debug - Configured Gemini with API key")

def call_llm(prompt: str) -> str:
    """Call Gemini API to analyze text
    
    Args:
        prompt (str): Input prompt for the model
        
    Returns:
        str: Model response
    """
    try:
        # Check for API key
        api_key = os.getenv("GOOGLE_API_KEY")
        print(f"Debug - API Key in call_llm: {api_key[:10]}..." if api_key else "No API key found in call_llm")
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found. Please set the environment variable.")
            
        print("Debug - Attempting to use Gemini")
        model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
        response = model.generate_content(prompt)
        print("Debug - Gemini response received")
        return response.text
            
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
        return ""

if __name__ == "__main__":
    # Test LLM call
    response = call_llm("What is web search?")
    print("Response:", response)
