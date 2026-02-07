# Repo GraphRAG MCP Usage Guide
"Repo GraphRAG MCP" extracts entities (classes, functions, etc.) and relationships from repository code and documentation to build a knowledge graph. Vectorizes and indexes all text. Combines graph search and vector search to answer questions and generate implementation plans with understanding of code structure.

## Prerequisites

- Python 3.11 or higher
- uv package manager

1. **Install dependencies**:
```bash
cd repo-graphrag-mcp
```

```bash
uv sync
```

2. **Configure environment variables**:
Copy `.env.example` to create a `.env` file


**Note**: Assumes users have already set up their environment. Refer to `repo-graphrag-mcp/.env.example` only when MCP startup or operation errors occur.

## Three Tools

1. **`graph_create`** - Analyze repository to build/update knowledge graph and vector index
2. **`graph_query`** - Answer questions about the repository using the knowledge graph
3. **`graph_plan`** - Generate implementation plans with understanding of existing code structure

All tools are invoked with the `graph:` prefix in user requests.

### Tool 1: graph_create

**Purpose**: Analyze a directory to build a knowledge graph and vector index.

**Parameters**:
- `read_dir_path` (required): Absolute path to the directory to analyze
- `storage_name` (optional): Name of the storage (default: "storage")

**Usage Examples**:
```
graph: /home/user/myproject my_project
graph: C:\projects\webapp webapp_storage
graph: /path/to/repo  # Uses default storage name "storage"
```

**Behavior**:
- First run: Processes all files and creates storage
- Subsequent runs: Processes only changed/new/deleted files (incremental update)
- Storage is created relative to the MCP server directory

**Processed File Types**:
Code files are fixed. Other types can be modified in `.env`.

- **Code**: .py, .cpp, .h, .java, .rs, .c, .cs, .go, .rb, .js, .jsx, .kt, .kts, .ts, .tsx, .html, .htm, .css
- **Documents** (default): .txt, .md, .rst, and special files: readme, changelog (case insensitive)
- **Excluded** (default): __pycache__, .git, .github, .venv, node_modules, .DS_Store, Thumbs.db, robots.txt, bac, backup, temp, tmp

**Incremental Update Notes**:
- If `EMBEDDING_MODEL_NAME` in `.env` is changed, storage deletion and recreation is required.
- If `DOC_DEFINITION_LIST` in `.env` is changed, recommend deleting and recreating storage for consistency.

**Performance Notes**:
- First run on large repositories (1000+ files) takes time. In such cases, ask users if they want to process subdirectories separately.
- Incremental updates are much faster as they only process changed/new/deleted files.

### Tool 2: graph_query

**Purpose**: Answer questions about the repository using the knowledge graph.

**Parameters**:
- `user_query` (required): Question to answer
- `storage_name` (optional): Storage to use (default: "storage")

**Usage Examples**:
```
graph: Tell me about API endpoints my_project
graph: my_project What are the main classes?
graph: Explain the database design webapp_storage
```

**Requirements**:
- Storage must exist (run `graph_create` first)
- Storage name is case-sensitive exact match

**Error Handling**:
- If storage not found: Notify user to run `graph_create` first

### Tool 3: graph_plan

**Purpose**: Generate implementation plans for modification/addition requests.

**Parameters**:
- `user_request` (required): Change/feature request
- `storage_name` (optional): Storage to use (default: "storage")

**Usage Examples**:
```
graph: Add user authentication my_project
graph: my_project Improve API error handling
graph: Refactor database layer webapp_storage
```

**Output**:
- Preparation steps
- Design considerations
- Implementation steps
- Cautions and recommendations

**Requirements**:
- Storage must exist (run `graph_create` first)
- Storage name is case-sensitive exact match

## Common User Scenarios

### Scenario 1: Initial Setup

1. User wants to analyze a project
2. Call `graph_create` with project path and storage name
3. Wait for completion (takes time for large repositories)
4. Storage is available for `graph_query` and `graph_plan`

### Scenario 2: Asking Questions

1. User has questions about the codebase
2. Verify storage exists
3. Call `graph_query` with the question
4. Return answer to user

### Scenario 3: Planning Changes

1. User wants to add features/fixes
2. Verify storage exists
3. Call `graph_plan` with the request
4. Present implementation plan to user & ask if they want to proceed with autonomous modifications

### Scenario 4: Configuration Changes

1. User requests configuration changes to `repo-graphrag-mcp`
2. Edit `.env` file
  - If `EMBEDDING_MODEL_NAME` is changed, existing storage deletion and recreation is **required**
  - If `DOC_DEFINITION_LIST` is changed, existing storage deletion and recreation is **recommended** for consistency

## Rate Limit Errors

**Cause**: Too many concurrent API calls.

**Solution**: Advise user to adjust in `.env`:
- Reduce `PARALLEL_NUM` (e.g., from 10 to 5)
- Increase `RATE_LIMIT_ERROR_WAIT_TIME` (e.g., from 60 to 120)

## Checking Logs

All operations are logged in `logs/mcp_server.log` in the MCP server directory.

**No need to actively read logs**
- Only when troubleshooting errors.

## Storage Location

- Storage is created in the MCP server directory (where `server.py` is located)
- Each storage is independent and can be used for different projects
