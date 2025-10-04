import os
from dotenv import load_dotenv
from tree_sitter import Language
import tree_sitter_python as tspython
import tree_sitter_cpp as tscpp
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjs
import tree_sitter_typescript as ts_typescript
import tree_sitter_rust as tsrust
import tree_sitter_c as tsc
import tree_sitter_go as tsgo
import tree_sitter_html as tshtml
import tree_sitter_ruby as tsruby
import tree_sitter_css as tscss
import tree_sitter_c_sharp as tscsharp
import tree_sitter_kotlin as tskotlin


# Load .env file
load_dotenv()

# Helper: get env var and cast to type
def get_config_value(key: str, default="__REQUIRED__", var_type=str):
    """Get env var and cast to the specified type."""
    value = os.getenv(key)
    
    # If not set
    if value is None:
        if default == "__REQUIRED__":
            raise ValueError(f"Environment variable {key} is not set. Please check your .env file.")
        # If default already matches the type, return as is
        if var_type != str and not isinstance(default, str):
            return default
        # Cast string default to the specified type
        if var_type == bool:
            # Bool: treat 'true', '1', 'yes', 'on' as True
            return str(default).lower() in ('true', '1', 'yes', 'on')
        elif var_type == int:
            # Int: cast default
            return int(default)
        elif var_type == float:
            # Float: cast default
            return float(default)
        else:
            # String/other: return default as is
            return default
    
    # Cast provided value
    if var_type == bool:
        # Bool: 'true', '1', 'yes', 'on' => True
        return value.lower() in ('true', '1', 'yes', 'on')
    elif var_type == int:
        # Int: cast string to int
        return int(value)
    elif var_type == float:
        # Float: cast string to float
        return float(value)
    else:
        # String/other: return string
        return value

# ==============================================================================
# API Keys & Provider Settings
# ==============================================================================
# LLM providers (separate for CREATE and ANALYSIS)
graph_create_provider = get_config_value("GRAPH_CREATE_PROVIDER", str)  # "anthropic" or "azure_openai" or "openai" or "gemini"
graph_analysis_provider = get_config_value("GRAPH_ANALYSIS_PROVIDER", str)  # "anthropic" or "azure_openai" or "openai" or "gemini"

# API keys per provider
anthropic_api_key = get_config_value("ANTHROPIC_API_KEY", None, str)
azure_openai_api_key = get_config_value("AZURE_OPENAI_API_KEY", None, str)
openai_api_key = get_config_value("OPENAI_API_KEY", None, str)
openai_base_url = get_config_value("OPENAI_BASE_URL", None, str)
gemini_api_key = get_config_value("GEMINI_API_KEY", None, str)

# Azure endpoint and API version (when using Azure provider)
azure_endpoint = get_config_value("AZURE_OPENAI_ENDPOINT", None, str)
azure_api_version = get_config_value("AZURE_API_VERSION", None, str)

# Providers in use
used_providers = {graph_create_provider, graph_analysis_provider}

# Validate required API keys for used providers
for provider in used_providers:
    if provider == "anthropic" and not anthropic_api_key:
        raise ValueError(f"Provider '{provider}' is selected but ANTHROPIC_API_KEY is not set.")
    elif provider == "azure_openai" and not azure_openai_api_key:
        raise ValueError(f"Provider '{provider}' is selected but AZURE_OPENAI_API_KEY is not set.")
    elif provider == "openai" and not (openai_api_key or openai_base_url):
        raise ValueError(f"Provider '{provider}' is selected but neither OPENAI_API_KEY nor OPENAI_BASE_URL is set.")
    elif provider == "gemini" and not gemini_api_key:
        raise ValueError(f"Provider '{provider}' is selected but GEMINI_API_KEY is not set.")

# ==============================================================================
# LLM Settings
# ==============================================================================
# Model names
graph_create_model_name = get_config_value("GRAPH_CREATE_MODEL_NAME")

graph_analysis_model_name = get_config_value("GRAPH_ANALYSIS_MODEL_NAME")

# Max output tokens for CREATE (entity extraction, summaries, etc.)
graph_create_max_token_size = get_config_value("GRAPH_CREATE_MAX_TOKEN_SIZE", "4096", int)

# Max output tokens for ANALYSIS (plans, answers, etc.)
graph_analysis_max_token_size = get_config_value("GRAPH_ANALYSIS_MAX_TOKEN_SIZE", "8192", int)

# ==============================================================================
# Embedding Settings
# ==============================================================================
embedding_model_name = get_config_value("EMBEDDING_MODEL_NAME", "BAAI/bge-m3", str)
embedding_dim = get_config_value("EMBEDDING_DIM", "1024", int)
embedding_max_token_size = get_config_value("EMBEDDING_MAX_TOKEN_SIZE", "2048", int)

# Optional Hugging Face Hub token (for authenticated/private models)
huggingface_hub_token = get_config_value("HUGGINGFACE_HUB_TOKEN", None, str)

# ==============================================================================
# Performance Settings
# ==============================================================================
# Concurrency
parallel_num = get_config_value("PARALLEL_NUM", "3", int)

# Chunk max tokens
chunk_max_tokens = get_config_value("CHUNK_MAX_TOKENS", "2048", int)

# Max depth when traversing Tree-sitter AST
max_depth = get_config_value("MAX_DEPTH", "30", int)

# Min request interval (sec)
rate_limit_min_interval = get_config_value("RATE_LIMIT_MIN_INTERVAL", "1.0", float)

# Wait time on rate-limit errors (sec)
rate_limit_error_wait_time = get_config_value("RATE_LIMIT_ERROR_WAIT_TIME", "3.0", float)

# ==============================================================================
# Planning/Query Settings
# ==============================================================================
# Retrieval/Search (GraphRAG)
search_top_k = get_config_value("SEARCH_TOP_K", "40", int)
search_mode = get_config_value("SEARCH_MODE", "mix", str)

# Token budgets (applied to both planning and query)
# Maximum total token budget for a single query context (entities + relations + chunks + system prompt)
max_total_tokens = get_config_value("MAX_TOTAL_TOKENS", "30000", int)

# Optional advanced budgets for entity and relation contexts
entity_max_tokens = get_config_value("MAX_ENTITY_TOKENS", "6000", int)
relation_max_tokens = get_config_value("MAX_RELATION_TOKENS", "8000", int)

# ==============================================================================
# Document Extensions
# ==============================================================================
# Extensions treated as documents
doc_ext_text_files_env = get_config_value("DOC_EXT_TEXT_FILES", "txt,md,rst", str)
doc_ext_text_files = [ext.strip() for ext in doc_ext_text_files_env.split(",") if ext.strip()]

# Special file names without extension
doc_ext_special_files_env = get_config_value("DOC_EXT_SPECIAL_FILES", "readme,changelog", str)
doc_ext_special_files = [file.strip().lower() for file in doc_ext_special_files_env.split(",") if file.strip()]

# Group non-code/doc files
doc_ext_dict = {
    "text_file": doc_ext_text_files,
    "special_files": doc_ext_special_files
}

# ==============================================================================
# Document Entity Extraction Settings
# ==============================================================================
# Entity types to extract from documents
document_definition_list_env = get_config_value("DOC_DEFINITION_LIST", "class_name,function_name,method_name", str)
document_definition_list = [item.strip() for item in document_definition_list_env.split(",") if item.strip()]

# ==============================================================================
# File/Directory Exclusion Settings
# ==============================================================================
# Files/directories to exclude
no_process_list_env = get_config_value("NO_PROCESS_LIST", "", str)
no_process_file_list = no_process_list_env.split(",") if no_process_list_env else [
    "__pycache__",
    ".git",
    ".github",
    ".venv", 
    "node_modules",
    ".DS_Store",
    "Thumbs.db",
    "robots.txt",
    "bac",
    "backup",
    "temp",
    "tmp"
]

# Remove empty entries
no_process_file_list = [item.strip() for item in no_process_file_list if item.strip()]

# ==============================================================================
# Tree-sitter Language Configurations
# ==============================================================================

# Python definition nodes to extract as entities (key: def type, value: node containing the name)
python_definition_dict = {
    "class_definition": "identifier",
    "function_definition": "identifier",
    "decorated_definition": "identifier"
}

# Tree-sitter for Python
py_lang = Language(tspython.language())

# C++ definition nodes to extract
cpp_definition_dict = {
    "class_specifier": "type_identifier",
    "struct_specifier": "type_identifier",
    "function_declarator": "identifier",
    "function_definition": "identifier",
    "namespace_definition": "namespace_identifier"
}

# Tree-sitter for C++
cpp_lang = Language(tscpp.language())

# Rust definition nodes to extract
rust_definition_dict = {
    "function_item": "identifier",
    "impl_item": "type_identifier",
    "struct_item": "type_identifier",
    "trait_item": "type_identifier"
}

# Tree-sitter for Rust
rust_lang = Language(tsrust.language())

# C definition nodes to extract
c_definition_dict = {
    "function_declarator": "identifier",
    "function_definition": "identifier",
    "struct_specifier": "type_identifier"
}

# Tree-sitter for C
c_lang = Language(tsc.language())

# C# definition nodes to extract
csharp_definition_dict = {
    "class_declaration": "identifier",
    "method_declaration": "identifier",
    "struct_declaration": "identifier",
    "interface_declaration": "identifier"
}

# Tree-sitter for C#
csharp_lang = Language(tscsharp.language())

# Go definition nodes to extract
go_definition_dict = {
    "function_declaration": "identifier",
    "method_declaration": "identifier",
    "type_declaration": "type_identifier",
    "interface_declaration": "type_identifier"
}

# Tree-sitter for Go
go_lang = Language(tsgo.language())

# Ruby definition nodes to extract
ruby_definition_dict = {
    "class": "constant",
    "module": "constant", 
    "method": "identifier",
    "singleton_method": "identifier"
}

# Tree-sitter for Ruby
ruby_lang = Language(tsruby.language())

# Java definition nodes to extract
java_definition_dict = {
    "class_declaration": "identifier",
    "method_declaration": "identifier",
    "interface_declaration": "identifier",
    "constructor_declaration": "identifier"
}

# Tree-sitter for Java
java_lang = Language(tsjava.language())

# Kotlin definition nodes to extract
kotlin_definition_dict = {
    "class_declaration": "identifier",
    "function_declaration": "identifier",
    "interface_declaration": "identifier",
    "object_declaration": "identifier",
    "primary_constructor": "identifier",
    "secondary_constructor": "identifier"
}

# Tree-sitter for Kotlin
kotlin_lang = Language(tskotlin.language())

# JavaScript definition nodes to extract
js_definition_dict = {
    "function_declaration": "identifier",
    "method_definition": "identifier",
    "class_declaration": "identifier"
}

# Tree-sitter for JavaScript
js_lang = Language(tsjs.language())

# TypeScript definition nodes to extract
ts_definition_dict = {
    "function_declaration": "identifier",
    "method_definition": "identifier",
    "class_declaration": "identifier",
    "interface_declaration": "identifier"
}

# Tree-sitter for TypeScript
ts_lang = Language(ts_typescript.language_typescript())

# HTML nodes to extract
html_definition_dict = {
    "style_element": "tag_name",
    "script_element": "tag_name"
}

# Tree-sitter for HTML
html_lang = Language(tshtml.language())

# CSS nodes to extract
css_definition_dict = {
    "rule_set": "selectors",
    "class_selector": "class_name",
    "id_selector": "id_name"
}

# Tree-sitter for CSS
css_lang = Language(tscss.language())

# Map file extensions to extraction config and Tree-sitter language
code_ext_dict = {
    "py": {
        "definition": python_definition_dict,
        "language": py_lang
    },
    "cpp": {
        "definition": cpp_definition_dict,
        "language": cpp_lang
    },
    "h": {
        "definition": cpp_definition_dict,
        "language": cpp_lang
    },
    "java": {
        "definition": java_definition_dict,
        "language": java_lang
    },
    "rs": {
        "definition": rust_definition_dict,
        "language": rust_lang
    },
    "c": {
        "definition": c_definition_dict,
        "language": c_lang
    },
    "cs": {
        "definition": csharp_definition_dict,
        "language": csharp_lang
    },
    "go": {
        "definition": go_definition_dict,
        "language": go_lang
    },
    "rb": {
        "definition": ruby_definition_dict,
        "language": ruby_lang
    },
    "js": {
        "definition": js_definition_dict,
        "language": js_lang
    },
    "kt": {
        "definition": kotlin_definition_dict,
        "language": kotlin_lang
    },
    "kts": {
        "definition": kotlin_definition_dict,
        "language": kotlin_lang
    },
    "jsx": {
        "definition": js_definition_dict,
        "language": js_lang
    },
    "ts": {
        "definition": ts_definition_dict,
        "language": ts_lang
    },
    "tsx": {
        "definition": ts_definition_dict,
        "language": ts_lang
    },
    "html": {
        "definition": html_definition_dict,
        "language": html_lang
    },
    "htm": {
        "definition": html_definition_dict,
        "language": html_lang
    },
    "css": {
        "definition": css_definition_dict,
        "language": css_lang
    }
}

# ==============================================================================
# LLM/Embedding Max Async Settings
# ==============================================================================
# Max concurrent requests for LLM and embedding match parallel_num
llm_model_max_async = parallel_num
embedding_func_max_async = parallel_num

# ==============================================================================
# Entity Merge Settings
# ==============================================================================
# Enable/disable entity merge
merge_enabled = get_config_value("MERGE_ENABLED", "true", bool)

# Cosine similarity threshold for merging
merge_score_threshold = get_config_value("MERGE_SCORE_THRESHOLD", "0.95", float)

# Entity Exclusion Patterns
_DEFAULT_MAGIC_METHODS = [
    '__init__', '__new__', '__del__', '__call__', '__str__', '__repr__',
    '__len__', '__getitem__', '__setitem__', '__delitem__', '__iter__',
    '__next__', '__contains__', '__add__', '__sub__', '__mul__', '__div__',
    '__truediv__', '__floordiv__', '__mod__', '__pow__', '__and__', '__or__',
    '__xor__', '__lshift__', '__rshift__', '__neg__', '__pos__', '__abs__',
    '__invert__', '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__',
    '__hash__', '__bool__', '__getattr__', '__setattr__', '__delattr__',
    '__enter__', '__exit__', '__with__', '__await__', '__aiter__', '__anext__'
]

magic_methods_env = get_config_value("MERGE_EXCLUDE_MAGIC_METHODS", "", str)
magic_methods_exclude_list = [item.strip() for item in magic_methods_env.split(",") if item.strip()] if magic_methods_env else _DEFAULT_MAGIC_METHODS

_DEFAULT_GENERIC_TERMS = [
    'data', 'result', 'value', 'item', 'element', 'object', 'instance',
    'index', 'key', 'name', 'text', 'string', 'number', 'count', 'size',
    'length', 'width', 'height', 'temp', 'tmp', 'test', 'example', 
    'sample', 'demo', 'main', 'app', 'init', 'config', 'util', 'helper',
    'manager', 'handler', 'controller', 'service'
]

generic_terms_env = get_config_value("MERGE_EXCLUDE_GENERIC_TERMS", "", str)
generic_terms_exclude_list = [item.strip() for item in generic_terms_env.split(",") if item.strip()] if generic_terms_env else _DEFAULT_GENERIC_TERMS

_DEFAULT_TEST_RELATED = [
    'foo', 'bar', 'baz', 'qux', 'spam', 'eggs', 'hello', 'world',
    'mock', 'stub', 'fake', 'dummy'
]

test_related_env = get_config_value("MERGE_EXCLUDE_TEST_RELATED", "", str)
test_related_exclude_list = [item.strip() for item in test_related_env.split(",") if item.strip()] if test_related_env else _DEFAULT_TEST_RELATED

# Exclude private entities (leading underscore)
merge_exclude_private_entities_enabled = get_config_value("MERGE_EXCLUDE_PRIVATE_ENTITIES_ENABLED", "true", bool)

# Custom exclusion patterns for entities
merge_exclude_custom_patterns_env = get_config_value("MERGE_EXCLUDE_CUSTOM_PATTERNS", "", str)
merge_exclude_custom_patterns = [pattern.strip() for pattern in merge_exclude_custom_patterns_env.split(",") if pattern.strip()] if merge_exclude_custom_patterns_env else []

# Min entity name length
merge_min_name_length = get_config_value("MERGE_MIN_NAME_LENGTH", 2, int)

# Max entity name length
merge_max_name_length = get_config_value("MERGE_MAX_NAME_LENGTH", 50, int)

