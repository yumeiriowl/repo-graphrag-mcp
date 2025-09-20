"""
Standalone entity merge tool

Usage:
uv run standalone_entity_merger.py <storage_dir_path>

Description:
- Merge all unmerged code entities and all document entities in the storage
- Automatically uses the existing MCP settings file (.env)
"""

import os
import sys
import asyncio
import logging
import traceback
from pathlib import Path


# Add MCP directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import modules from repo-graphrag-mcp environment
try:
    from repo_graphrag.initialization.initializer import initialize_rag
    from repo_graphrag.processors.entity_merger import should_exclude_entity, merge_doc_and_code
    from repo_graphrag.config.settings import (
        merge_score_threshold, 
        parallel_num, 
        code_ext_dict
    )
    from lightrag import LightRAG
    
except ImportError as e:
    logger.error(f"Failed to import repo-graphrag-mcp modules or required libraries: {e}")
    logger.info("Run within the repo-graphrag-mcp directory and ensure required libraries are installed.")
    sys.exit(1)

async def main():
    """Main routine"""
    original_argv = sys.argv.copy()
    sys.argv = [original_argv[0]]  
    
    if len(original_argv) != 2:
        print("Usage: uv run standalone_entity_merger.py <storage_dir_path>")
        print("Example: uv run standalone_entity_merger.py ./storage_dir")
        sys.exit(1)
    
    storage_path = original_argv[1]
    
    try:
        logger.info(f"Initializing LightRAG with MCP settings: {storage_path}")
        logger.info(f"Merge threshold: {merge_score_threshold}")
        logger.info(f"Parallelism: {parallel_num}")
        
        # Initialize LightRAG
        rag = await initialize_rag(storage_path)
        
        # Prepare all unmerged code entities
        current_code_dict = await prepare_unmerged_code_dict(rag)
        
        # Execute entity merge
        await merge_doc_and_code(rag, current_code_dict)
        
        logger.info("Entity merge completed successfully")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
       
def is_unmerged_code_entity(entity_name: str, entity_file_path: str) -> bool:
    """
    Determine whether it is an unmerged code entity
    """
    if not entity_file_path:
        return False
        
    # Check file extension
    _, ext = os.path.splitext(entity_file_path)
    if ext.lstrip(".") not in code_ext_dict:
        return False
    
    # Check if it has the format "filename:definition"
    has_colon_format = (':' in entity_name and 
                       not entity_name.startswith(':') and 
                       not entity_name.endswith(':'))
    
    # Exclude merged entities (those that contain <SEP>)
    is_already_merged = '<SEP>' in entity_file_path
    
    return has_colon_format and not is_already_merged

async def prepare_unmerged_code_dict(rag: LightRAG) -> dict:
    """
    Prepare a dictionary of file paths for unmerged code entities
    """
    logger.info("=" * 50)
    
    # Get names of all entities
    all_entity_name = await rag.get_graph_labels()
    
    # Collect file paths of unmerged code entities
    code_file_paths = set()
    
    for entity_name in all_entity_name:
        # Skip entities that should be excluded
        if should_exclude_entity(entity_name):
            continue
        
        # Get entity info from the entity name
        entity = await rag.chunk_entity_relation_graph.get_node(entity_name)
        if not entity:
            logger.warning(f"Entity not found: {entity_name}")
            continue
            
        entity_file_path = entity.get("file_path")
        
        # Check unmerged code entity
        if is_unmerged_code_entity(entity_name, entity_file_path):
            code_file_paths.add(entity_file_path)
    
    # Convert the set of file paths to a dict
    current_code_dict = {file_path: True for file_path in code_file_paths}
    
    return current_code_dict

if __name__ == "__main__":
    asyncio.run(main())
