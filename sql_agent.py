"""
SQL Agent implementation using LangChain for database querying.
Based on the LangChain SQL agent tutorial.
"""

import os
import re
from typing import Optional
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent
from document_store import DocumentStore


class LoggingSQLDatabase(SQLDatabase):
    """Wrapper around SQLDatabase that logs all SQL queries."""
    
    def _log_query(self, command: str):
        """Helper method to log SQL queries."""
        print(f"\n🔍 Executing SQL Query on 'ot_cdc' database:")
        print(f"   {command}")
        print()
    
    def run(self, command: str, fetch: str = "all", **kwargs) -> str:
        """
        Execute SQL command and log it.
        
        Args:
            command: SQL command to execute
            fetch: How to fetch results ('all', 'one', 'cursor')
            **kwargs: Additional arguments passed to parent run method
            
        Returns:
            Query results
        """
        self._log_query(command)
        return super().run(command, fetch=fetch, **kwargs)
    
    def run_no_throw(self, command: str, fetch: str = "all", **kwargs) -> str:
        """
        Execute SQL command without throwing exceptions, and log it.
        
        Args:
            command: SQL command to execute
            fetch: How to fetch results ('all', 'one', 'cursor')
            **kwargs: Additional arguments passed to parent run_no_throw method
            
        Returns:
            Query results or error message
        """
        self._log_query(command)
        return super().run_no_throw(command, fetch=fetch, **kwargs)


class SQLAgent:
    """A LangChain-powered SQL agent for querying databases."""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the SQL Agent.
        
        Args:
            database_url: Database connection string. Defaults to MySQL ot_cdc database.
        """
        if database_url:
            self.database_url = database_url
        else:
            # Build MySQL connection string from environment variables
            mysql_host = os.getenv("MYSQL_HOST", "localhost")
            mysql_user = os.getenv("MYSQL_USER", "root")
            mysql_password = os.getenv("MYSQL_PASSWORD", "root")
            mysql_database = os.getenv("MYSQL_DATABASE", "ot_cdc")
            
            self.database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_database}"
        
        self.db = None
        self.agent = None
        self.document_store = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the database connection and agent."""
        try:
            # Initialize the database connection with limited schema info to save tokens
            print(f"🔗 Connecting to database: {self.database_url}")
            
            # Try to limit to commonly used tables to reduce context size
            # Start with ordhdr (order header) which is the primary table
            common_tables = ["ordhdr"]  # Add more tables here if needed
            
            try:
                # First, get all available tables
                temp_db = SQLDatabase.from_uri(self.database_url)
                all_tables = temp_db.get_usable_table_names()
                
                # If we have many tables, try to limit to common ones plus a few others
                # This helps reduce the schema size in the context
                if len(all_tables) > 10:
                    # Use include_tables to limit schema to most common tables
                    # This significantly reduces token usage
                    include_tables = common_tables + [t for t in all_tables if t.startswith("ord")][:5]
                    # Use LoggingSQLDatabase to log queries - create base DB then wrap it
                    base_db = SQLDatabase.from_uri(
                        self.database_url,
                        include_tables=include_tables,
                        sample_rows_in_table_info=0,
                    )
                    # Create logging wrapper by copying attributes
                    self.db = LoggingSQLDatabase.from_uri(
                        self.database_url,
                        include_tables=include_tables,
                        sample_rows_in_table_info=0,
                    )
                    print(f"⚠️  Limited to {len(include_tables)} tables to reduce context size")
                else:
                    # If we have few tables, include all of them
                    # Use LoggingSQLDatabase to log queries
                    self.db = LoggingSQLDatabase.from_uri(
                        self.database_url,
                        sample_rows_in_table_info=0,
                    )
            except Exception:
                # Fallback: include all tables if limiting fails
                self.db = LoggingSQLDatabase.from_uri(
                    self.database_url,
                    sample_rows_in_table_info=0,
                )
            
            # Initialize the document store for query history and semantic search
            print("🧠 Initializing document store...")
            self.document_store = DocumentStore()
            
            # Initialize the LLM
            print("🤖 Initializing language model...")
            self.model = init_chat_model("openai:gpt-4")
            
            # Create the SQL toolkit
            toolkit = SQLDatabaseToolkit(db=self.db, llm=self.model)
            tools = toolkit.get_tools()
            
            # Sanitize tool names to match OpenAI's function name pattern (^[a-zA-Z0-9_-]+$)
            # OpenAI requires function names to only contain alphanumeric, underscore, and hyphen
            def sanitize_function_name(name: str) -> str:
                """Sanitize function name to match OpenAI's pattern."""
                if not name:
                    return "unnamed_tool"
                # Replace any characters that aren't alphanumeric, underscore, or hyphen
                sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
                # Remove consecutive underscores
                sanitized = re.sub(r'_+', '_', sanitized)
                # Ensure it doesn't start with a number or hyphen
                if sanitized and (sanitized[0].isdigit() or sanitized[0] == '-'):
                    sanitized = 'tool_' + sanitized
                # Ensure it doesn't end with underscore or hyphen
                sanitized = sanitized.rstrip('_-')
                # Ensure it's not empty
                if not sanitized:
                    sanitized = "unnamed_tool"
                return sanitized
            
            for tool in tools:
                if hasattr(tool, 'name'):
                    original_name = tool.name
                    sanitized_name = sanitize_function_name(original_name)
                    
                    if sanitized_name != original_name:
                        tool.name = sanitized_name
                        # Update function name if it exists
                        if hasattr(tool, 'func') and hasattr(tool.func, '__name__'):
                            tool.func.__name__ = sanitized_name
                        # Update any internal references
                        if hasattr(tool, '_name'):
                            tool._name = sanitized_name
                        # Update binding if it exists (for structured tools)
                        if hasattr(tool, 'binding') and hasattr(tool.binding, 'function'):
                            if hasattr(tool.binding.function, 'name'):
                                tool.binding.function.name = sanitized_name
                        # Update args_schema title if it exists
                        try:
                            if hasattr(tool, 'args_schema') and tool.args_schema:
                                if hasattr(tool.args_schema, 'schema'):
                                    schema = tool.args_schema.schema()
                                    if isinstance(schema, dict) and 'title' in schema:
                                        schema['title'] = sanitized_name
                        except Exception:
                            pass  # Ignore errors when accessing schema
            
            # Create minimal system prompt to save tokens
            system_prompt = """You are a MySQL agent for 'ot_cdc' database. Create correct queries, execute them, return answers.

Rules: Limit to {top_k} results. Query only relevant columns. Check tables/schemas first. Verify queries before execution. NO DML (INSERT/UPDATE/DELETE/DROP).""".format(
                top_k=10,
            )
            
            # Create the agent
            self.agent = create_agent(
                self.model,
                tools,
                system_prompt=system_prompt,
            )
            
            print("✅ SQL Agent initialized successfully!")
            
        except Exception as e:
            raise Exception(f"Failed to initialize SQL Agent: {str(e)}")
    
    def query(self, question: str) -> str:
        """
        Query the database with a natural language question.
        
        Args:
            question: Natural language question about the data
            
        Returns:
            Formatted response with the query results
        """
        try:
            # Search for relevant documentation to guide query generation
            # This helps the agent use proper SQL patterns from the documentation
            enhanced_question = question
            doc_context = ""
            
            if self.document_store:
                # Search for relevant documentation (not query history)
                relevant_docs = self.document_store.search_documentation(question, limit=1)
                
                if relevant_docs:
                    doc = relevant_docs[0]
                    # Extract SQL examples from the documentation content
                    import re
                    content = doc.get("content", "")
                    
                    # Try to find SQL in code blocks first
                    sql_examples = re.findall(r'```sql\s*\n(.*?)\n```', content, re.DOTALL)
                    if not sql_examples:
                        # Try without language tag
                        sql_examples = re.findall(r'```\s*\n(.*?)\n```', content, re.DOTALL)
                    if not sql_examples:
                        # Try to find SQL queries without code blocks (multi-line SELECT)
                        sql_examples = re.findall(r'(SELECT[\s\S]*?;)', content, re.IGNORECASE)
                    
                    if sql_examples:
                        # Use the most relevant SQL example (prefer shorter, more focused ones)
                        # Sort by length and take a medium-sized one (not too short, not too long)
                        sql_examples.sort(key=len)
                        best_example = None
                        for example in sql_examples:
                            # Prefer examples that are 100-400 chars (good balance)
                            if 100 <= len(example) <= 400:
                                best_example = example
                                break
                        if not best_example:
                            # Fall back to first example, truncated
                            best_example = sql_examples[0][:400]
                        
                        doc_title = doc.get("title", "Documentation")
                        doc_context = f"\n\nUse this SQL pattern from {doc_title} as a guide:\n```sql\n{best_example.strip()}\n```"
                        enhanced_question = question + doc_context
            
            # Run the agent with the enhanced question
            response = self.agent.invoke({"messages": [{"role": "user", "content": enhanced_question}]})
            
            # Extract the final message content
            if "messages" in response and response["messages"]:
                result = response["messages"][-1].content
                
                # Store this query in the document store for future learning
                if self.document_store:
                    # Extract SQL query from the response (this is a simple approach)
                    sql_query = self._extract_sql_from_response(result)
                    self.document_store.store_query_history(question, sql_query, result, success=True)
                
                return result
            else:
                return "I couldn't process your question. Please try rephrasing it."
                
        except Exception as e:
            error_str = str(e)
            
            # Handle context length errors with helpful message
            if "context_length_exceeded" in error_str or "maximum context length" in error_str.lower():
                error_msg = """The database schema is too large for the current model context. 

Try:
1. Ask about a specific table (e.g., 'Show orders from ordhdr table')
2. Use 'tables' command to see available tables first
3. Ask more specific questions about fewer tables at once

The database has many tables with detailed schemas that exceed the token limit."""
            else:
                error_msg = f"Error processing your question: {error_str}"
            
            # Store failed query for learning
            if self.document_store:
                self.document_store.store_query_history(question, "", error_msg, success=False)
            
            return error_msg
    
    def _extract_sql_from_response(self, response: str) -> str:
        """
        Extract SQL query from agent response (simple approach).
        
        Args:
            response: Agent response text
            
        Returns:
            Extracted SQL query or empty string
        """
        # Simple regex to find SQL queries in the response
        import re
        
        # Look for SQL queries between backticks or in code blocks
        sql_patterns = [
            r'```sql\n(.*?)\n```',
            r'```\n(.*?)\n```',
            r'`(SELECT.*?)`',
            r'(SELECT.*?;)',
        ]
        
        for pattern in sql_patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return ""
    
    def get_available_tables(self) -> list:
        """Get list of available tables in the database."""
        try:
            return self.db.get_usable_table_names()
        except Exception as e:
            print(f"Error getting tables: {str(e)}")
            return []
    
    def get_table_schema(self, table_name: str) -> str:
        """Get schema information for a specific table."""
        try:
            return self.db.get_table_info([table_name])
        except Exception as e:
            return f"Error getting schema for {table_name}: {str(e)}"
    
    def add_document(self, title: str, content: str, doc_type: str = "document") -> bool:
        """
        Add a document to the document store for semantic search.
        
        Args:
            title: Document title
            content: Document content
            doc_type: Type of document (e.g., "manual", "specification", "example")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.document_store:
                return self.document_store.store_document(title, content, doc_type)
            return False
        except Exception as e:
            print(f"Error adding document: {e}")
            return False
    
    def get_query_suggestions(self, partial_query: str) -> list:
        """
        Get query suggestions based on partial input.
        
        Args:
            partial_query: Partial query text
            
        Returns:
            List of suggested query completions
        """
        try:
            if self.document_store:
                return self.document_store.get_query_suggestions(partial_query)
            return []
        except Exception as e:
            print(f"Error getting query suggestions: {e}")
            return []
    
    def get_document_stats(self) -> dict:
        """
        Get statistics about stored documents and queries.
        
        Returns:
            Dictionary with document store statistics
        """
        try:
            if self.document_store:
                return self.document_store.get_stats()
            return {}
        except Exception as e:
            print(f"Error getting document stats: {e}")
            return {}
