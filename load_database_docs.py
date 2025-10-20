"""
Script to load database documentation into the document store for semantic search.
"""

import os
import glob
from pathlib import Path
from dotenv import load_dotenv
from sql_agent import SQLAgent

# Load environment variables
load_dotenv()


def load_database_docs():
    """Load all database documentation files into the document store."""
    try:
        print("🚀 Loading Database Documentation into Document Store")
        print("=" * 60)
        
        # Initialize the agent
        agent = SQLAgent()
        
        # Find all markdown files in the database_docs directory
        docs_dir = Path("database_docs")
        if not docs_dir.exists():
            print(f"❌ Documentation directory {docs_dir} not found!")
            return False
        
        markdown_files = list(docs_dir.glob("*.md"))
        
        if not markdown_files:
            print(f"❌ No markdown files found in {docs_dir}")
            return False
        
        print(f"📁 Found {len(markdown_files)} documentation files:")
        
        success_count = 0
        for file_path in markdown_files:
            print(f"\n📄 Loading: {file_path.name}")
            
            try:
                # Read the file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract title from filename or first line
                title = file_path.stem.replace('_', ' ').title()
                
                # Determine document type
                doc_type = "table_documentation" if "table" in file_path.name else "database_documentation"
                
                # Store in document store
                success = agent.add_document(title, content, doc_type)
                
                if success:
                    print(f"   ✅ Successfully loaded: {title}")
                    success_count += 1
                else:
                    print(f"   ❌ Failed to load: {title}")
                    
            except Exception as e:
                print(f"   ❌ Error loading {file_path.name}: {e}")
        
        print(f"\n📊 Loading Summary:")
        print(f"   Total files: {len(markdown_files)}")
        print(f"   Successfully loaded: {success_count}")
        print(f"   Failed: {len(markdown_files) - success_count}")
        
        if success_count > 0:
            print(f"\n🎉 Database documentation loaded successfully!")
            print(f"   The agent can now use this information to better understand your database.")
            
            # Show stats
            stats = agent.get_document_stats()
            if stats:
                print(f"\n📈 Document Store Statistics:")
                print(f"   Total documents: {stats.get('total_documents', 0)}")
                print(f"   Documentation files: {stats.get('documents', 0)}")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error loading database documentation: {e}")
        return False


def create_sample_docs():
    """Create sample documentation files if they don't exist."""
    docs_dir = Path("database_docs")
    docs_dir.mkdir(exist_ok=True)
    
    print("📁 Creating database_docs directory...")
    print("   Please add your database documentation files to the 'database_docs' directory.")
    print("   Supported formats: .md (Markdown)")
    print("   The script will automatically load all .md files from this directory.")


def main():
    """Main function to load database documentation."""
    print("🤖 Reports Extension Agent - Database Documentation Loader")
    print("=" * 60)
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key in the .env file or environment.")
        return
    
    # Check if database_docs directory exists
    docs_dir = Path("database_docs")
    if not docs_dir.exists():
        create_sample_docs()
        return
    
    # Load documentation
    success = load_database_docs()
    
    if success:
        print(f"\n✅ Setup complete!")
        print(f"   You can now run 'python main.py' to start using the agent.")
        print(f"   The agent will have access to your database documentation for better query generation.")
    else:
        print(f"\n⚠️  Setup incomplete. Please check the errors above.")


if __name__ == "__main__":
    main()
