# Changelog

## 0.2.4 - 2026-02-07

### Added
- AGENTS.md usage guide for MCP agents.

## 0.2.3 - 2026-02-07

### Changed
- Dependency updates and related code changes.

## 0.2.2 - 2025-10-04

### Added
- Kotlin language support (tree-sitter-kotlin) with `.kt` and `.kts` entity extraction.

## 0.2.1 - 2025-10-04

### Added
- `OPENAI_BASE_URL` environment variable to support OpenAI-compatible endpoints (e.g. LM Studio). Allows use without `OPENAI_API_KEY` for local endpoints.

## 0.2.0 - 2025-09-21

### Added
- MCP tools: `graph_create`, `graph_plan`, `graph_query`
 - Standalone execution: `standalone_graph_creator.py` (graph creation), `standalone_entity_merger.py` (entity merge)