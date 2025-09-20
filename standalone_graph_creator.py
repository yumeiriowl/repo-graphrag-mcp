"""
Standalone graph creation tool

Usage:
uv run standalone_graph_creator.py <read_dir_path> <storage_dir_path>

Description:
- Create GraphRAG storage from the specified directory
- Automatically uses the existing MCP settings file (.env)
"""

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
    from repo_graphrag.graph_storage_creator import create_graph_storage
    
except ImportError as e:
    logger.error(f"Failed to import repo-graphrag-mcp modules: {e}")
    logger.info("Run within the repo-graphrag-mcp directory and ensure required libraries are installed.")
    sys.exit(1)

async def main():
    """Main routine"""
    original_argv = sys.argv.copy()
    sys.argv = [original_argv[0]]
    
    if len(original_argv) != 3:
        print("Usage: uv run standalone_graph_creator.py <read_dir_path> <storage_dir_path>")
        print("Example: uv run standalone_graph_creator.py ./input_dir ./storage_dir")
        sys.exit(1)
    
    read_dir_path = original_argv[1]
    storage_dir_path = original_argv[2]
    
    try:
        logger.info("Starting GraphRAG storage creation")
        logger.info(f"Read directory: {read_dir_path}")
        logger.info(f"Storage directory: {storage_dir_path}")
        
        # Create graph storage
        await create_graph_storage(read_dir_path, storage_dir_path)
        
        logger.info("Storage creation completed successfully")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
