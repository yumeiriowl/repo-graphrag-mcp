# Repo GraphRAG MCP Server

Repo GraphRAG MCP Server is an MCP (Model Context Protocol) server that uses LightRAG and Tree-sitter to build a knowledge graph from code and text-based documents (text-only; PDFs/Word/Excel are not parsed) in a repository/directory, and leverages it for Q&A and implementation planning.
It provides tools for graph building (`graph_create`), implementation planning (`graph_plan`), and Q&A (`graph_query`).

- 📊 Knowledge graph creation (`graph_create`): Analyze code/documents to build a knowledge graph and embedding index (supports incremental updates)
- 🔧 Implementation planning (`graph_plan`): Output implementation plans and concrete change steps for modification/addition requests based on the knowledge graph (optionally combined with vector search)
- 🔍 Q&A (`graph_query`): Answer questions based on the knowledge graph (optionally combined with vector search)

## Table of Contents

- [🚀 Quick Start](#-quick-start)
  - [1. Installation](#1-installation)
  - [2. Environment Setup](#2-environment-setup)
  - [3. Environment Variables (LLM Setup)](#3-environment-variables-llm-setup)
  - [4. MCP Client Setup](#4-mcp-client-setup)
  - [5. Usage](#5-usage)
- [⚙️ Configuration Options](#%EF%B8%8F-configuration-options)
  - [LLM Providers](#llm-providers)
  - [Embedding Model](#embedding-model)
  - [Planning/Query Settings for graph_plan and graph_query](#planningquery-settings-for-graph_plan-and-graph_query)
  - [Entity Merge](#entity-merge)
  - [Detailed Environment Variables](#detailed-environment-variables)
- [🧬 Supported Languages](#-supported-languages-v020)
- [🏗️ MCP Structure](#-mcp-structure)
- [🛠️ Standalone Execution](#%EF%B8%8F-standalone-execution)
- [🙏 Acknowledgments](#-acknowledgments)
- [📄 License](#-license)

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- Credentials for your chosen LLM provider (set the required environment variables; see the LLM Providers section below)

### 1. Installation

```bash
# Clone from GitHub
git clone https://github.com/yumeiriowl/repo-graphrag-mcp.git
cd repo-graphrag-mcp

# Install dependencies
uv sync
```

### 2. Environment Setup

```bash
# Copy the settings file
cp .env.example .env

# Edit the settings file
nano .env  # or any editor
```

### 3. Environment Variables (LLM Setup)

Configure settings in the `.env` file:

#### Example: Using Anthropic models
```bash
# LLM provider for graph creation
GRAPH_CREATE_PROVIDER=anthropic  # or openai, gemini, azure_openai

# Provider for planning and Q&A
GRAPH_ANALYSIS_PROVIDER=anthropic # or openai, gemini, azure_openai

# API keys (set the variables corresponding to your chosen provider)
ANTHROPIC_API_KEY=your_anthropic_api_key # or openai, gemini, azure_openai

# AZURE_OPENAI_API_KEY=your_azure_openai_api_key
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_API_VERSION=azure_openai_api_version

# OPENAI_API_KEY=your_openai_api_key

# GEMINI_API_KEY=your_gemini_api_key

# LLM model for graph creation
GRAPH_CREATE_MODEL_NAME=claude-3-5-haiku-20241022

# LLM model for planning and Q&A
GRAPH_ANALYSIS_MODEL_NAME=claude-sonnet-4-20250514
```

### 4. MCP Client Setup

#### Claude Code

```bash
claude mcp add repo-graphrag \
-- uv --directory /absolute/path/to/repo-graphrag-mcp run server.py
```

#### VS Code GitHub Copilot Extensions

`mcp.json`:
```json
{
  "servers": {
    "repo-graphrag-server": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/repo-graphrag-mcp",
        "run",
        "server.py"
      ]
    }
  }
}
```

#### Other MCP Clients

Any client that supports the MCP protocol can be used.

### 5. Usage

The following tools are available in MCP clients. All commands must start with `graph:`.

#### `graph_create` - Build/Update Knowledge Graph

Analyze the target repository/directory and build a knowledge graph and vector embedding index (supports incremental updates). Uses `GRAPH_CREATE_PROVIDER` and `GRAPH_CREATE_MODEL_NAME`.

Elements:
- `graph:` (required)
- Directory path to analyze (absolute path recommended)
- Storage name to create (default: "storage")

Examples:
```
graph: /path/to/your/repository my_project
graph: /path/to/your/repository my_project graphify
graph: C:\\projects\\myapp webapp_storage please create storage
```

About Incremental Updates:
When you run `graph_create` again with an existing storage name, only changed/added/deleted files are reanalyzed; others are skipped.
If you want to rebuild after changing the embedding model or extraction settings (DOC_DEFINITION_LIST, NO_PROCESS_LIST, target extensions, etc.), delete the existing storage or specify a new storage name and recreate with `graph_create` or `standalone_graph_creator.py`.

Note (Performance):
The first graph creation takes longer as the number of files increases. As a guideline, if there are more than 1,000 files, consider narrowing the target directory (processing time depends on environment and file sizes).
Incremental updates reanalyze only the diffs, so this note does not apply to updates.

Note (First download):
If the specified embedding model is not cached on first graph creation, it will be automatically downloaded (subsequent runs use the cache).

#### `graph_plan` - Implementation Support

Based on the knowledge graph (optionally combined with vector search), provide a detailed implementation plan and instructions so that the MCP client (agent) can perform actual work. Uses `GRAPH_ANALYSIS_PROVIDER` and `GRAPH_ANALYSIS_MODEL_NAME`.

Elements:
- `graph:` (required)
- Implementation/modification request
- Storage name (default: "storage")

Examples:
```
graph: I want to add user authentication my_project
graph: Add GraphQL support to the REST API my_project
graph: Create a performance improvement plan webapp_storage
```

#### `graph_query` - Q&A

Based on the knowledge graph (optionally combined with vector search), answer questions about the target repository/directory. Uses `GRAPH_ANALYSIS_PROVIDER` and `GRAPH_ANALYSIS_MODEL_NAME`.

Elements:
- `graph:` (required)
- Question content
- Storage name (default: "storage")

Examples:
```
graph: Tell me about this project's API endpoints my_project
graph: my_project Explain the main classes and their roles
graph: About the database design webapp_storage
```

## ⚙️ Configuration Options

### LLM Providers

Supported providers and required environment variables

| Provider | Identifier | Required environment variables |
|---|---|---|
| Anthropic Claude | `anthropic` | `ANTHROPIC_API_KEY` |
| OpenAI GPT | `openai` | `OPENAI_API_KEY` |
| Google Gemini | `gemini` | `GEMINI_API_KEY` |
| Azure OpenAI | `azure_openai` | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_API_VERSION` |

Specify the identifiers in `.env` as `GRAPH_CREATE_PROVIDER` / `GRAPH_ANALYSIS_PROVIDER`.

### Embedding Model

- Default: `BAAI/bge-m3`
- Compatibility: Supports Hugging Face sentence-transformers compatible models
 - First run: If the specified embedding model is not cached, it will be downloaded automatically. Cache location depends on environment/settings. Download time and disk space depend on model size.
 - Authenticated models: For Hugging Face models that require authentication, set `HUGGINGFACE_HUB_TOKEN` in `.env`.

    ```bash
    HUGGINGFACE_HUB_TOKEN=your_hf_token
    ```

### Planning/Query Settings for `graph_plan` and `graph_query`

Implementation note: The settings in this section are passed directly to LightRAG's built-in `QueryParam`. This MCP does not implement custom retrieval or token-budgeting logic; it reuses LightRAG's behavior as-is.

#### Retrieval/Search Modes

Search modes follow LightRAG. Set one of the following in `.env` `SEARCH_MODE`.

- `mix`: Combination of vector search and knowledge graph search (recommended)
- `hybrid`: Combination of local and global search
- `naive`: Simple vector search
- `local`: Community-based search
- `global`: Global community search

#### Token Budgets (Input-side)

Input-side token budgets control how much context is assembled for planning and Q&A (LightRAG `QueryParam`). These are independent from model output token limits.

- `MAX_TOTAL_TOKENS`: Overall input context budget per query (entities + relations + retrieved chunks + system prompt). Default: `30000`.
- `MAX_ENTITY_TOKENS`: Budget for entity context (input-side). Default: `6000`.
- `MAX_RELATION_TOKENS`: Budget for relation context (input-side). Default: `8000`.

Note: Output token limits are controlled separately via `GRAPH_ANALYSIS_MAX_TOKEN_SIZE` (for planning/Q&A) and `GRAPH_CREATE_MAX_TOKEN_SIZE` (for graph creation tasks). If you increase input budgets significantly, ensure your model's total context window can accommodate both input and output.

### Entity Merge

This MCP can merge entities extracted from documents with entities extracted from code based on semantic similarity. The goal is to unify references (e.g., a class or function defined in code and mentioned in documentation) into a single consolidated entity.

- How it works: Names are normalized and filtered via exclusion rules; document entities and current-pass code entities are embedded and compared using cosine similarity (FAISS). Pairs above the threshold are merged, consolidating descriptions and file paths.
- Controls:
  - `MERGE_ENABLED` (default: `true`): Toggle entity merge.
  - `MERGE_SCORE_THRESHOLD` (default: `0.95`): Cosine similarity threshold for merging.
  - Exclusion settings: `MERGE_EXCLUDE_*` lists, private name exclusion, name length bounds, and custom patterns.
- Execution:
  - When enabled, merge runs within the graph creation/update flow (after entity extraction).
  - You can also run the standalone tool: `uv run standalone_entity_merger.py <storage_dir_path>`

### Detailed Environment Variables

All environment variables and defaults can be configured by copying `.env.example` to `.env`.

Quick reference for all items

| Variable | Purpose/Description |
|---|---|
| `GRAPH_CREATE_PROVIDER` | LLM provider for graph creation |
| `GRAPH_ANALYSIS_PROVIDER` | LLM provider for planning/Q&A |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL |
| `AZURE_API_VERSION` | Azure OpenAI API version |
| `OPENAI_API_KEY` | OpenAI API key |
| `GEMINI_API_KEY` | Google Gemini API key |
| `GRAPH_CREATE_MODEL_NAME` | LLM model name for graph creation |
| `GRAPH_ANALYSIS_MODEL_NAME` | LLM model name for planning/Q&A |
| `GRAPH_CREATE_MAX_TOKEN_SIZE` | Max output tokens for LLM during graph creation |
| `GRAPH_ANALYSIS_MAX_TOKEN_SIZE` | Max output tokens for LLM during planning/Q&A |
| `MAX_TOTAL_TOKENS` | Overall input-side token budget per planning/query (entities + relations + chunks + system) |
| `MAX_ENTITY_TOKENS` | Input-side token budget for entity context |
| `MAX_RELATION_TOKENS` | Input-side token budget for relation context |
| `EMBEDDING_MODEL_NAME` | Embedding model name (Hugging Face) |
| `EMBEDDING_DIM` | Embedding vector dimension |
| `EMBEDDING_MAX_TOKEN_SIZE` | Max token length for embedding |
| `HUGGINGFACE_HUB_TOKEN` | HF auth token (optional) |
| `PARALLEL_NUM` | Parallelism (concurrent LLM/embedding tasks) |
| `CHUNK_MAX_TOKENS` | Max tokens per chunk |
| `MAX_DEPTH` | Max Tree-sitter traversal depth |
| `RATE_LIMIT_MIN_INTERVAL` | Minimum interval between API calls (seconds) |
| `RATE_LIMIT_ERROR_WAIT_TIME` | Wait time on rate limit errors (seconds) |
| `SEARCH_TOP_K` | Number of results to retrieve in search |
| `SEARCH_MODE` | Search mode (`naive`/`local`/`global`/`hybrid`/`mix`) |
| `DOC_EXT_TEXT_FILES` | Extensions treated as document (text) files (comma-separated) |
| `DOC_EXT_SPECIAL_FILES` | Special filenames without extension (text) (comma-separated) |
| `DOC_DEFINITION_LIST` | Entity types to extract from documents |
| `NO_PROCESS_LIST` | Files/directories to exclude (comma-separated) |
| `MERGE_ENABLED` | Enable entity merge (true/false) |
| `MERGE_SCORE_THRESHOLD` | Cosine similarity threshold for merge |
| `MERGE_EXCLUDE_MAGIC_METHODS` | Exclusion list for magic methods |
| `MERGE_EXCLUDE_GENERIC_TERMS` | Exclusion list for generic terms |
| `MERGE_EXCLUDE_TEST_RELATED` | Exclusion list for test-related terms |
| `MERGE_EXCLUDE_PRIVATE_ENTITIES_ENABLED` | Exclude private entities (leading underscore) (true/false) |
| `MERGE_EXCLUDE_CUSTOM_PATTERNS` | Additional exclusion patterns (wildcards allowed) |
| `MERGE_MIN_NAME_LENGTH` | Minimum entity name length for merge |
| `MERGE_MAX_NAME_LENGTH` | Maximum entity name length for merge |

## 🧬 Supported Languages (v0.2.0)

The following 12 languages are supported:

- Python
- C
- C++
- Rust
- C#
- Go
- Ruby
- Java
- JavaScript
- TypeScript
- HTML
- CSS

## 🏗️ MCP Structure

```
repo-graphrag-mcp/
├── README.md
├── CHANGELOG.md              # Changelog
├── LICENSE                   # License (MIT)
├── pyproject.toml            # Package settings
├── server.py                 # MCP server entrypoint
├── .env.example              # Environment variable template
├── standalone_graph_creator.py   # Standalone graph builder
├── standalone_entity_merger.py   # Standalone entity merger
├── repo_graphrag/            # Package
│   ├── config/               # Configuration
│   ├── initialization/       # Initialization
│   ├── llm/                  # LLM clients
│   ├── processors/           # Analysis/graph building
│   ├── utils/                # Utilities
│   ├── graph_storage_creator.py  # Storage creation
│   └── prompts.py            # Prompts
└── logs/                     # Log output
```

## 🛠️ Standalone Execution

You can also run without an MCP client:

### standalone_graph_creator.py - Build Knowledge Graph

Analyze a repository and create a knowledge graph:

```bash
uv run standalone_graph_creator.py <read_dir_path> <storage_name>
```

Examples:
```bash
uv run standalone_graph_creator.py /home/user/myproject my_storage
uv run standalone_graph_creator.py C:\\projects\\webapp webapp_storage
```

### standalone_entity_merger.py - Entity Merge

Merge entities within an existing storage:

```bash
uv run standalone_entity_merger.py <storage_dir_path>
```

Examples:
```bash
uv run standalone_entity_merger.py /home/user/myproject/my_storage
uv run standalone_entity_merger.py C:\\projects\\webapp/webapp_storage
```

Note:
- The storage directory must be created beforehand by `graph_create` or `standalone_graph_creator.py`.

## 🙏 Acknowledgments

This MCP is built on the following libraries:
- [LightRAG](https://github.com/HKUDS/LightRAG) - GraphRAG implementation
- [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) - Code parsing

## 📄 License

This MCP is released under the MIT License. See the [LICENSE](LICENSE) file for details.