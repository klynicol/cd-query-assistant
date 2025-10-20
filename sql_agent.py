"""
SQL Agent implementation using LangChain for database querying.
Based on the LangChain SQL agent tutorial.
"""

import os
from typing import Optional
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent
from document_store import DocumentStore


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
            # Initialize the database connection
            print(f"🔗 Connecting to database: {self.database_url}")
            self.db = SQLDatabase.from_uri(self.database_url)
            
            # Initialize the document store for query history and semantic search
            print("🧠 Initializing document store...")
            self.document_store = DocumentStore()
            
            # Initialize the LLM
            print("🤖 Initializing language model...")
            self.model = init_chat_model("openai:gpt-4")
            
            # Create the SQL toolkit
            toolkit = SQLDatabaseToolkit(db=self.db, llm=self.model)
            tools = toolkit.get_tools()
            
            # Create the system prompt with metadata context
            system_prompt = """
You are an agent designed to interact with a MySQL database called 'ot_cdc'.
Given an input question, create a syntactically correct MySQL query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {top_k} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

You MUST double check your query before executing it. If you get an error while
executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
database.

To start you should ALWAYS look at the tables in the database to see what you
can query. Do NOT skip this step.

Then you should query the schema of the most relevant tables.

The database contains business data including order headers (ordhdr table) and 
related tables. You can learn from previous successful queries stored in the
document store to improve your responses.

If the user asks about data they don't have access to, politely inform them
that you can only query the available database tables and suggest they check
their permissions or contact their administrator.

Use the document store to find similar queries and learn from successful
query patterns to generate better SQL queries.
""".format(
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
            # First, look for similar queries in the document store
            similar_queries = []
            if self.document_store:
                similar_queries = self.document_store.search_similar_queries(question, limit=3)
            
            # Enhance the question with context from similar queries
            enhanced_question = question
            if similar_queries:
                context = "\n\nSimilar successful queries:\n"
                for similar in similar_queries:
                    if similar["success"]:
                        context += f"- Query: {similar['query']}\n  SQL: {similar['sql_query']}\n"
                enhanced_question = question + context
            
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
            error_msg = f"Error processing your question: {str(e)}"
            
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
