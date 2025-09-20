import asyncio
from typing import List, Tuple
from tree_sitter import Node
from ..initialization.initializer import get_tokenizer
from ..config.settings import chunk_max_tokens


async def create_code_chunks(root_node: Node, file_content_bytes: bytes) -> List[Tuple[Node, str]]:
    """
    Extract nodes to be used as code chunks.
    
    Args:
        root_node: Tree-sitter root node
        file_content_bytes: File content as bytes
    
    Returns:
        list: List of tuples (node, text) for chunking
    """
    # Initialize queue for nodes
    task_queue = asyncio.Queue()   

    # Enqueue direct children of the root
    for child_node in root_node.children:
        await task_queue.put(child_node)

    chunk_node_list = []
    tokenizer = get_tokenizer()
    
    while not task_queue.empty():
        
        # Dequeue a node
        current_node = await task_queue.get()

        # Get the code text for the node span
        node_text = file_content_bytes[current_node.start_byte:current_node.end_byte].decode("utf-8").strip()

        # Skip empty nodes
        if not node_text:
            continue

        # Tokenize the code text
        tokens = await asyncio.to_thread(tokenizer.encode, node_text)

        # If within the configured max token size, accept as a chunk
        if chunk_max_tokens >= len(tokens):
            chunk_node_list.append((current_node, node_text))
        else:
            # Otherwise, enqueue children for finer-grained chunking
            for child_node in current_node.children:
                await task_queue.put(child_node)

    # Return extracted nodes for chunking
    return chunk_node_list
