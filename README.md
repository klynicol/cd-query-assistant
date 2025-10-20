# Reports Extension Agent

A LangChain-powered agent for querying MySQL databases based on natural language questions. This agent uses Milvus Lite to store document embeddings and query history, enabling semantic search and learning from successful queries.

## Features

- 🤖 Natural language to SQL query generation for MySQL databases
- 🧠 Milvus Lite integration for document embeddings and query history storage
- 📚 Semantic search over query history and documents
- 🔍 Query suggestions based on similar successful queries
- 🔒 Database access control awareness (user_groups support planned)
- 📊 Designed for `ot_cdc` database with `ordhdr` table
- 🔧 Easy setup and configuration
- 🎯 Based on LangChain's SQL agent tutorial and 13-minute example

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

Copy the example environment file and add your API keys:

```bash
cp env.example .env
```

Edit `.env` and configure your database connection:

```env
OPENAI_API_KEY=your_openai_api_key_here
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=ot_cdc
```

### 3. Load Database Documentation

Create documentation files describing your database schema and load them into the agent:

```bash
python load_database_docs.py
```

This will load documentation from the `database_docs/` directory into the document store for semantic search.

### 4. Run the Agent

```bash
python main.py
```

## Usage

Once the agent is running, you can ask questions like:

- "Show me recent orders from the ordhdr table"
- "What are the top customers by order value?"
- "How many orders were placed this month?"
- "What tables are available in the database?"

### Available Commands

- `tables` - List all available tables
- `stats` - Show document store statistics (query history, documents)
- `suggestions <partial_query>` - Get query suggestions based on similar queries
- `help` - Show available commands

## Project Structure

```
reports_extension/
├── main.py                 # Main entry point
├── sql_agent.py           # SQL agent implementation
├── document_store.py      # Milvus Lite document embeddings storage
├── load_database_docs.py  # Load database documentation into document store
├── database_docs/         # Database documentation files (.md)
│   ├── ordhdr_table.md   # Order header table documentation
│   ├── table_relationships.md  # Table relationships and joins
│   └── query_examples.md # Common query examples
├── requirements.txt       # Python dependencies
├── env.example           # Environment variables template
├── milvus_demo.db        # Milvus Lite database (created automatically)
└── README.md             # This file
```

## Database Schema

The agent is designed to work with your `ot_cdc` MySQL database, specifically:

- **ordhdr**: Order header table (primary focus)
- **Additional tables**: Discovered automatically from your database

The agent uses Milvus Lite to store:
- **Database documentation**: Schema descriptions, table relationships, and query examples
- **Query history**: Successful queries and their results for learning
- **Document embeddings**: Business documents, manuals, specifications, etc.
- **Query patterns**: Learned patterns from user interactions
- **Semantic search**: Find similar queries and relevant documentation to improve responses

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `MYSQL_HOST`: MySQL server host (default: localhost)
- `MYSQL_USER`: MySQL username (default: root)
- `MYSQL_PASSWORD`: MySQL password (default: root)
- `MYSQL_DATABASE`: MySQL database name (default: ot_cdc)

### Using Different Databases

You can connect to different MySQL databases by modifying the environment variables or passing a custom database URL:

```python
# Custom MySQL connection
agent = SQLAgent("mysql+pymysql://user:password@host:port/database")
```

## Extending the Agent

### Adding Database Documentation

The best way to help the agent understand your database is to create documentation files:

1. **Create documentation files**: Add `.md` files to the `database_docs/` directory describing:
   - Table structures and purposes
   - Column descriptions and data types
   - Table relationships and join patterns
   - Common query examples
   - Business rules and constraints

2. **Load documentation**: Run `python load_database_docs.py` to store the documentation in Milvus

3. **Query history**: The agent automatically stores successful queries for future reference

4. **Semantic search**: Find similar queries and relevant documentation to improve responses

### User Access Control (Future)

The agent is designed to support user-based access control:

1. **user_groups table**: Planned integration with your existing user groups
2. **Query filtering**: Automatically filter results based on user permissions
3. **Access validation**: Check user permissions before executing queries

### Advanced Features

- **Semantic search**: Find similar queries and documents using vector embeddings
- **Query optimization**: Learn from successful queries to improve performance
- **Document storage**: Store and search through business documents and manuals
- **Custom tools**: Add domain-specific tools for your business logic

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**: Make sure your API key is set in the `.env` file
2. **MySQL Connection Error**: Check your MySQL credentials and ensure the database exists
3. **Import Errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
4. **Milvus Lite Error**: The `milvus_demo.db` file is created automatically on first run
5. **No Tables Found**: Ensure your `ot_cdc` database exists and contains the `ordhdr` table

### Getting Help

If you encounter issues:

1. Check the error messages in the console
2. Verify your environment variables
3. Ensure your database is accessible
4. Check that all dependencies are installed

## License

This project is for prototyping and demonstration purposes.
# cd-query-assistant
# cd-query-assistant
