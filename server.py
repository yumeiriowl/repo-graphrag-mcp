import os
import gc
import logging
from logging.handlers import RotatingFileHandler
from mcp.server.fastmcp import FastMCP
from lightrag import QueryParam
from repo_graphrag.config.settings import (
    search_top_k,
    search_mode,
    max_total_tokens,
    entity_max_tokens,
    relation_max_tokens,
)
from repo_graphrag.initialization.initializer import initialize_rag
from repo_graphrag.graph_storage_creator import create_graph_storage
from repo_graphrag.prompts import (
    PLAN_PROMPT_TEMPLATE,
    PLAN_RESPONSE_TEMPLATE,
    QUERY_RESPONSE_TEMPLATE,
    GRAPH_STORAGE_RESULT_TEMPLATE,
    STORAGE_NOT_FOUND_ERROR_TEMPLATE,
    GENERAL_ERROR_TEMPLATE
)


# Define custom formatter
class CustomFormatter(logging.Formatter):
    def format(self, record):
        if record.getMessage().strip() in ('', '\n'):
            return ''
        return super().format(record)

# Create log directory
log_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(log_dir, exist_ok=True)

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configure handler
handler = RotatingFileHandler(
    os.path.join(log_dir, 'mcp_server.log'),
    maxBytes=1048576,
    backupCount=5
)

# Set custom formatter
formatter = CustomFormatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Helper function to output a blank line
def log_newline():
    """Write a simple newline to the log file"""
    with open(os.path.join(log_dir, 'mcp_server.log'), 'a', encoding='utf-8') as f:
        f.write('\n')

mcp = FastMCP("repo-graphrag-server")

@mcp.tool()
async def graph_create(
    read_dir_path: str,
    storage_name: str = "storage"
) -> str:
    """
    Read documents and code from the specified directory and create GraphRAG storage.
    Always call this tool when instructions include "graph:" and request graph creation or storage creation/update for a project.
    
    Args:
        read_dir_path: Directory path to read
        storage_name: Storage directory name to create (default: "storage")
        
    Returns:
        str: Result message
        
    Examples:
        - "graph: create graph <read_dir_path> <storage_name>"
        - "graph: create storage <storage_name> <read_dir_path>"
        - "<storage_name> <read_dir_path> graphify graph:"
    """
    
    log_newline()
    logging.getLogger().info("=" * 80)
    logging.getLogger().info("graph_create tool start")
    logging.getLogger().info("=" * 80)
    
    try:
        # Set the storage directory path based on the MCP server directory
        server_dir = os.path.dirname(os.path.abspath(__file__))
        storage_dir_path = os.path.join(server_dir, storage_name)
        
        # Check if storage exists
        storage_exists = os.path.exists(storage_dir_path)
        action = "updated" if storage_exists else "created"
        
        # Create graph storage
        await create_graph_storage(read_dir_path, storage_dir_path)
        
        result_message = GRAPH_STORAGE_RESULT_TEMPLATE.format(
            read_dir_path=read_dir_path, 
            storage_dir_path=storage_dir_path, 
            action=action
        )
        
        logger.info("")
        logging.getLogger().info("=" * 80)
        logging.getLogger().info("graph_create tool completed")
        logging.getLogger().info("=" * 80)
        log_newline()
        
        return result_message
    
    except Exception as e:
        error_message = GENERAL_ERROR_TEMPLATE.format(error=str(e))
        
        logger.info("")
        logging.getLogger().error("=" * 80)
        logging.getLogger().error("graph_create tool error")
        logging.getLogger().error("=" * 80)
        log_newline()
        
        return error_message

@mcp.tool()
async def graph_plan(user_request: str, storage_name: str = "storage") -> str:
    """
    A tool that returns a plan text for modification/addition requests.
    Always call this tool when instructions include "graph:" with modifications/additions/fixes/changes/new feature requests.
    Do not include "graph:" and storage_name in user_request.
    
    Args: 
        user_request (str) = Modification/addition request (exclude unrelated text)
        storage_name (str) = Storage directory name (default: "storage")

    Returns: str = Implementation plan text
        - Steps for "Preparation", "Design", and "Implementation"
        - Notes
        
    Examples:
        - "graph: add a new process to the design document <storage_name>"
        - "graph: <storage_name> I want to change API specifications"
        - "<storage_name> I want to fix bugs or refactor graph:"
    """
    
    log_newline()
    logging.getLogger().info("=" * 80)
    logging.getLogger().info("graph_plan tool start")
    logging.getLogger().info("=" * 80)
    
    # Set the storage directory path based on the MCP server directory
    server_dir = os.path.dirname(os.path.abspath(__file__))
    storage_dir_path = os.path.join(server_dir, storage_name)
        
    # Check storage directory exists
    if not os.path.exists(storage_dir_path):
        
        logging.getLogger().info("")
        logging.getLogger().error("=" * 80)
        logging.getLogger().error("graph_plan tool error: storage not found")
        logging.getLogger().error("=" * 80)
        log_newline()
        
        return STORAGE_NOT_FOUND_ERROR_TEMPLATE.format(storage_name=storage_name)

    CREATE_PLAN_PROMPT = PLAN_PROMPT_TEMPLATE.format(user_request=user_request)

    rag = await initialize_rag(storage_dir_path)
    query_param = QueryParam(
        mode=search_mode,
        user_prompt=CREATE_PLAN_PROMPT,
        top_k=search_top_k,
        max_total_tokens=max_total_tokens,
        max_entity_tokens=entity_max_tokens,
        max_relation_tokens=relation_max_tokens,
    )
    try:
        # Create plan
        plan = await rag.aquery(
            query=user_request, 
            param=query_param
        )
    finally:
        await rag.finalize_storages()
        
        # Drop cache
        await rag.llm_response_cache.drop()
            
        # Cleanup instance
        del rag
        
        # Attempt global state cleanup
        gc.collect()

    result_message = PLAN_RESPONSE_TEMPLATE.format(
        user_request=user_request, 
        plan=plan, 
        storage_name=storage_name
    )
    
    logging.getLogger().info("")
    logging.getLogger().info("=" * 80)
    logging.getLogger().info("graph_plan tool completed")
    logging.getLogger().info("=" * 80)
    log_newline()
    
    return result_message

@mcp.tool()
async def graph_query(user_query: str, storage_name: str = "storage") -> str:
    """
    A tool that returns an answer text for a question.
    Always call this tool when instructions include "graph:" and a question is asked.
    Do not include "graph:" and storage_name in user_query.
    
    Args:
        user_query (str) = Question (exclude unrelated text)
        storage_name (str) = Storage directory name (default: "storage")
    
    Returns:
        str: Answer text
        
    Examples:
        - "graph: Tell me the process in the design document <storage_name>"
        - "graph: <storage_name> I want to know the API specifications"
        - "<storage_name> How to fix bugs or refactor graph:"
    """
    
    log_newline()
    logging.getLogger().info("=" * 80)
    logging.getLogger().info("graph_query tool start")
    logging.getLogger().info("=" * 80)
    
    # Set the storage directory path based on the MCP server directory
    server_dir = os.path.dirname(os.path.abspath(__file__))
    storage_dir_path = os.path.join(server_dir, storage_name)
        
    # Check storage directory exists
    if not os.path.exists(storage_dir_path):
        
        logging.getLogger().info("")
        logging.getLogger().error("=" * 80)
        logging.getLogger().error("graph_query tool error: storage not found")
        logging.getLogger().error("=" * 80)
        log_newline()
        
        return STORAGE_NOT_FOUND_ERROR_TEMPLATE.format(storage_name=storage_name)

    rag = await initialize_rag(storage_dir_path)
    query_param = QueryParam(
        mode=search_mode,
        top_k=search_top_k,
        max_total_tokens=max_total_tokens,
        max_entity_tokens=entity_max_tokens,
        max_relation_tokens=relation_max_tokens,
    )
    try:
        # Create answer
        response = await rag.aquery(
            query=user_query, 
            param=query_param
        )
    finally:
        await rag.finalize_storages()
        
        # Drop cache
        await rag.llm_response_cache.drop()
            
        # Cleanup instance
        del rag
        
        # Attempt global state cleanup
        gc.collect()
        
    result_message = QUERY_RESPONSE_TEMPLATE.format(
        user_query=user_query, 
        response=response, 
        storage_name=storage_name
    )
    
    logging.getLogger().info("")
    logging.getLogger().info("=" * 80)
    logging.getLogger().info("graph_query tool completed")
    logging.getLogger().info("=" * 80)
    log_newline()
    
    return result_message


if __name__ == "__main__":
    mcp.run(transport="stdio")
