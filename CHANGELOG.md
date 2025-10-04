# Changelog

## 0.2.1 - 2025-10-04

### Added
- `OPENAI_BASE_URL` environment variable to support OpenAI-compatible endpoints (e.g. LM Studio). Allows use without `OPENAI_API_KEY` for local endpoints.

## 0.2.0 - 2025-09-21

### Added
- MCP tools: `graph_create`, `graph_plan`, `graph_query`
 - Standalone execution: `standalone_graph_creator.py` (graph creation), `standalone_entity_merger.py` (entity merge)