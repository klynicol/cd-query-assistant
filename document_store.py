"""
Document and query history storage using Milvus Lite for semantic search.
Based on the LangChain 13-minute example approach.
"""

import os
import json
from typing import List, Dict, Any, Optional
from pymilvus import MilvusClient
from datetime import datetime


class DocumentStore:
    """Manages document embeddings and query history in Milvus for semantic search."""
    
    def __init__(self, milvus_db_path: str = "milvus_demo.db"):
        """
        Initialize the document store with Milvus Lite.
        
        Args:
            milvus_db_path: Path to the Milvus Lite database file
        """
        self.client = MilvusClient(milvus_db_path)
        self.collection_name = "documents"
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Initialize the documents collection if it doesn't exist."""
        try:
            # Create collection for storing document embeddings
            # Using dimension 1536 for OpenAI text-embedding-ada-002
            self.client.create_collection(
                collection_name=self.collection_name,
                dimension=1536,  # OpenAI embedding dimension
                metric_type="COSINE",  # Cosine similarity for text similarity
                consistency_level="Strong"
            )
            print(f"✅ Created Milvus collection: {self.collection_name}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"📁 Milvus collection {self.collection_name} already exists")
            else:
                print(f"⚠️  Milvus collection creation warning: {e}")
    
    def store_query_history(self, query: str, sql_query: str, result: str, success: bool = True) -> bool:
        """
        Store a query and its result for learning purposes.
        
        Args:
            query: Natural language query from user
            sql_query: Generated SQL query
            result: Query result or error message
            success: Whether the query was successful
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a document text for embedding
            doc_text = f"Query: {query}\nSQL: {sql_query}\nResult: {result[:500]}..."  # Truncate long results
            
            # Generate embedding using OpenAI (you'll need to implement this)
            embedding = self._get_embedding(doc_text)
            
            # Create document data
            doc_id = self._generate_doc_id(query, sql_query)
            timestamp = datetime.now().isoformat()
            
            data = {
                "id": doc_id,
                "vector": embedding,
                "query": query,
                "sql_query": sql_query,
                "result": result,
                "success": success,
                "timestamp": timestamp,
                "doc_type": "query_history"
            }
            
            self.client.insert(
                collection_name=self.collection_name,
                data=[data]
            )
            
            print(f"✅ Stored query history: {query[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Error storing query history: {e}")
            return False
    
    def store_document(self, title: str, content: str, doc_type: str = "document") -> bool:
        """
        Store a document with its embedding.
        
        Args:
            title: Document title
            content: Document content
            doc_type: Type of document (e.g., "manual", "specification", "example")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embedding
            embedding = self._get_embedding(content)
            
            # Create document data
            doc_id = self._generate_doc_id(title, content)
            timestamp = datetime.now().isoformat()
            
            data = {
                "id": doc_id,
                "vector": embedding,
                "query": title,
                "sql_query": "",
                "result": content,
                "success": True,
                "timestamp": timestamp,
                "doc_type": doc_type
            }
            
            self.client.insert(
                collection_name=self.collection_name,
                data=[data]
            )
            
            print(f"✅ Stored document: {title}")
            return True
            
        except Exception as e:
            print(f"❌ Error storing document: {e}")
            return False
    
    def search_similar_queries(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar queries based on the input query.
        
        Args:
            query: Natural language query to search for
            limit: Maximum number of results
            
        Returns:
            List of similar queries with their SQL and results
        """
        try:
            # Generate embedding for the query
            query_embedding = self._get_embedding(query)
            
            # Search in Milvus
            results = self.client.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                limit=limit,
                output_fields=["query", "sql_query", "result", "success", "timestamp", "doc_type"]
            )
            
            # Format results
            formatted_results = []
            if not results or len(results) == 0:
                return []
            
            for result in results[0]:  # results is a list of lists
                try:
                    # Handle different Milvus result structures
                    # Score might be in result["distance"] or result["score"]
                    similarity_score = 0.0
                    if "distance" in result:
                        similarity_score = result["distance"]
                    elif "score" in result:
                        similarity_score = result["score"]
                    
                    # Handle entity data - might be nested or flat
                    entity_data = result.get("entity", result)
                    if not isinstance(entity_data, dict):
                        entity_data = result
                    
                    formatted_results.append({
                        "query": entity_data.get("query", ""),
                        "sql_query": entity_data.get("sql_query", ""),
                        "result": entity_data.get("result", ""),
                        "success": entity_data.get("success", True),
                        "timestamp": entity_data.get("timestamp", ""),
                        "doc_type": entity_data.get("doc_type", "query_history"),
                        "similarity_score": similarity_score
                    })
                except (KeyError, TypeError) as e:
                    # Skip malformed results
                    print(f"⚠️  Skipping malformed search result: {e}")
                    continue
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching similar queries: {e}")
            return []
    
    def search_documentation(self, query: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        Search for relevant documentation (not query history).
        
        Args:
            query: Natural language query to search for
            limit: Maximum number of results
            
        Returns:
            List of relevant documentation with SQL examples
        """
        try:
            # Generate embedding for the query
            query_embedding = self._get_embedding(query)
            
            # Search in Milvus (get more results to filter manually)
            results = self.client.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                limit=limit * 3,  # Get more to filter
                output_fields=["query", "sql_query", "result", "success", "timestamp", "doc_type"]
            )
            
            # Format results
            formatted_results = []
            if not results or len(results) == 0:
                return []
            
            for result in results[0]:  # results is a list of lists
                try:
                    entity_data = result.get("entity", result)
                    if not isinstance(entity_data, dict):
                        entity_data = result
                    
                    # Only include documentation, not query history
                    doc_type = entity_data.get("doc_type", "")
                    if doc_type == "query_history":
                        continue
                    
                    similarity_score = 0.0
                    if "distance" in result:
                        similarity_score = result["distance"]
                    elif "score" in result:
                        similarity_score = result["score"]
                    
                    formatted_results.append({
                        "title": entity_data.get("query", ""),  # Title is stored in "query" field for docs
                        "content": entity_data.get("result", ""),  # Content is stored in "result" field for docs
                        "doc_type": doc_type,
                        "similarity_score": similarity_score
                    })
                    
                    if len(formatted_results) >= limit:
                        break
                        
                except (KeyError, TypeError) as e:
                    continue
            
            return formatted_results
            
        except Exception as e:
            # If filter doesn't work, fall back to regular search and filter manually
            try:
                all_results = self.search_similar_queries(query, limit=limit * 2)
                return [r for r in all_results if r.get("doc_type") != "query_history"][:limit]
            except Exception:
                return []
    
    def get_query_suggestions(self, partial_query: str) -> List[str]:
        """
        Get query suggestions based on partial input.
        
        Args:
            partial_query: Partial query text
            
        Returns:
            List of suggested query completions
        """
        try:
            similar_queries = self.search_similar_queries(partial_query, limit=10)
            suggestions = []
            
            for result in similar_queries:
                if result["success"] and result["doc_type"] == "query_history":
                    suggestions.append(result["query"])
            
            # Remove duplicates and return top suggestions
            return list(set(suggestions))[:5]
            
        except Exception as e:
            print(f"❌ Error getting query suggestions: {e}")
            return []
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        try:
            from openai import OpenAI
            
            # Initialize OpenAI client
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Generate embedding
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            # Fallback to simple hash-based embedding
            return self._simple_text_embedding(text)
    
    def _simple_text_embedding(self, text: str) -> List[float]:
        """
        Fallback simple text embedding (hash-based).
        Used when OpenAI embedding fails.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        import hashlib
        
        # Create a hash of the text
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert to a list of floats (1536 dimensions for OpenAI compatibility)
        embedding = []
        for i in range(0, len(text_hash), 2):
            # Convert hex pairs to normalized floats
            hex_pair = text_hash[i:i+2]
            value = int(hex_pair, 16) / 255.0  # Normalize to 0-1
            embedding.append(value)
        
        # Pad or truncate to exactly 1536 dimensions
        while len(embedding) < 1536:
            embedding.append(0.0)
        
        return embedding[:1536]
    
    def _generate_doc_id(self, title: str, content: str) -> int:
        """
        Generate a unique integer ID for a document.
        
        Args:
            title: Document title
            content: Document content
            
        Returns:
            Integer ID
        """
        import hashlib
        
        # Create a hash of title and content
        combined = f"{title}:{content}"
        doc_hash = hashlib.md5(combined.encode()).hexdigest()
        
        # Convert to integer (using first 8 characters)
        return int(doc_hash[:8], 16)
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about stored documents."""
        try:
            # Query all documents to get stats
            # Milvus requires a filter with limit, so we'll use a filter that matches everything
            # Try to get all documents by using a filter that's always true
            try:
                results = self.client.query(
                    collection_name=self.collection_name,
                    filter='doc_type in ["query_history", "document", "table_documentation", "database_documentation"]',
                    output_fields=["doc_type", "success"],
                    limit=10000
                )
            except Exception:
                # If filter doesn't work, try without filter but with limit
                try:
                    results = self.client.query(
                        collection_name=self.collection_name,
                        output_fields=["doc_type", "success"],
                        limit=10000
                    )
                except Exception:
                    # If that fails, return empty stats
                    return {"total_documents": 0, "query_history": 0, "documents": 0, "successful_queries": 0, "failed_queries": 0}
            
            stats = {
                "total_documents": len(results),
                "query_history": 0,
                "documents": 0,
                "successful_queries": 0,
                "failed_queries": 0
            }
            
            for result in results:
                if result["doc_type"] == "query_history":
                    stats["query_history"] += 1
                    if result["success"]:
                        stats["successful_queries"] += 1
                    else:
                        stats["failed_queries"] += 1
                elif result["doc_type"] == "document":
                    stats["documents"] += 1
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {"total_documents": 0}


if __name__ == "__main__":
    # Test the document store
    store = DocumentStore()
    
    # Test storing a query history
    test_query = "Show me recent orders"
    test_sql = "SELECT * FROM ordhdr ORDER BY order_date DESC LIMIT 10"
    test_result = "Found 10 recent orders..."
    
    store.store_query_history(test_query, test_sql, test_result, success=True)
    
    # Test storing a document
    store.store_document(
        "Order Header Table Guide",
        "The ordhdr table contains order header information including order ID, customer details, order date, and total amount. Use this table to query order information.",
        "manual"
    )
    
    # Test search
    results = store.search_similar_queries("recent orders", limit=3)
    print("Search results:", results)
    
    # Test stats
    stats = store.get_stats()
    print("Stats:", stats)
    
    print("✅ Document store test completed!")
