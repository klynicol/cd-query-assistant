"""
Reports Extension Agent - A LangChain-powered agent for querying databases
based on user questions about data they have access to.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from sql_agent import SQLAgent


def main():
    """Main entry point for the Reports Extension Agent."""
    print("🤖 Reports Extension Agent")
    print("=" * 50)
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key in the .env file or environment.")
        print("You can copy env.example to .env and fill in your API key.")
        return
    
    try:
        # Initialize the SQL agent
        print("🔄 Initializing SQL Agent...")
        agent = SQLAgent()
        
        print("✅ Agent ready!")
        print("\n💡 You can now ask questions about the data in your ot_cdc database.")
        print("   Example: 'Show me recent orders from the ordhdr table'")
        print("   Example: 'What tables are available?'")
        print("   Type 'quit' or 'exit' to stop.")
        print("   Type 'help' for more commands.")
        print("   The agent learns from your queries to improve over time!\n")
        
        # Interactive loop
        while True:
            try:
                question = input("🤔 Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if question.lower() == 'help':
                    print("\n📚 Available commands:")
                    print("   - Ask questions about your data")
                    print("   - 'tables' - List available tables")
                    print("   - 'stats' - Show document store statistics")
                    print("   - 'suggestions <partial_query>' - Get query suggestions")
                    print("   - 'quit' or 'exit' - Stop the agent")
                    print()
                    continue
                
                if question.lower() == 'tables':
                    tables = agent.get_available_tables()
                    print(f"\n📋 Available tables: {', '.join(tables) if tables else 'No tables found'}")
                    print()
                    continue
                
                if question.lower() == 'stats':
                    stats = agent.get_document_stats()
                    if stats:
                        print(f"\n📊 Document Store Statistics:")
                        print(f"   Total documents: {stats.get('total_documents', 0)}")
                        print(f"   Query history: {stats.get('query_history', 0)}")
                        print(f"   Documents: {stats.get('documents', 0)}")
                        print(f"   Successful queries: {stats.get('successful_queries', 0)}")
                        print(f"   Failed queries: {stats.get('failed_queries', 0)}")
                    else:
                        print("\n📊 No statistics available")
                    print()
                    continue
                
                if question.lower().startswith('suggestions'):
                    parts = question.split(' ', 1)
                    if len(parts) > 1:
                        partial_query = parts[1]
                        suggestions = agent.get_query_suggestions(partial_query)
                        if suggestions:
                            print(f"\n💡 Query suggestions for '{partial_query}':")
                            for i, suggestion in enumerate(suggestions, 1):
                                print(f"   {i}. {suggestion}")
                        else:
                            print(f"\n💡 No suggestions found for '{partial_query}'")
                    else:
                        print("\n💡 Usage: suggestions <partial_query>")
                    print()
                    continue
                
                if not question:
                    continue
                
                print("\n🔄 Processing your question...")
                response = agent.query(question)
                print(f"\n📊 Answer: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
    
    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
