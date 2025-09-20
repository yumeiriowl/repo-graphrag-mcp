import os
import asyncio
from typing import Dict, List, Tuple, Any
from tree_sitter import Node
from ..config.settings import max_depth
from ..llm.llm_client import complete_graph_create
from ..utils.node_line_range import get_node_line_range
from ..prompts import CODE_SUMMARY_PROMPT_TEMPLATE


async def create_code_graph(
    node: Node,
    definition_dict: Dict[str, str],
    file_content_bytes: bytes,
    parent_definition_name: str,
    source_id: str,
    code_path: str,
    line_offset_list: List[int]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extract graphable nodes (entities and relationships) from code.
    
    Args:
        node: Tree-sitter node
        definition_dict: Mapping of node type -> definition-name node type
        file_content_bytes: File content (bytes)
        parent_definition_name: Parent definition name
        source_id: Source identifier
        code_path: Code file path
        line_offset_list: List of line-start byte offsets
    
    Returns:
        tuple: (entities, relationships)
    """
    entities = []
    relationships = []
    
    file_name = os.path.basename(code_path)
    
    # Initialize queue with tuples (node, parent-name, depth)
    task_queue = asyncio.Queue()

    # Seed the queue
    await task_queue.put((node, parent_definition_name, 0))

    while not task_queue.empty():
        current_node, parent_definition_name, depth = await task_queue.get()

    # Get code fragment for the node
        node_text = file_content_bytes[current_node.start_byte:current_node.end_byte].decode("utf-8").strip()

        # Skip empty fragments
        if not node_text: 
            continue

    # Initialize definition name with parent's
        definition_name = parent_definition_name

        # If node type is in definition list, generate an entity
        if current_node.type in definition_dict:
            start_line, end_line = get_node_line_range(current_node, line_offset_list)

            # Prepare queue for searching child nodes
            search_queue = asyncio.Queue()
            for child in current_node.children:
                await search_queue.put(child)

            entity_name = ""

            # Find the child node that carries the definition name
            while not search_queue.empty():
                search_node = await search_queue.get()
                if search_node.type == definition_dict[current_node.type]:
                    definition_name = file_content_bytes[search_node.start_byte:search_node.end_byte].decode('utf-8').strip()
                    entity_name = f"{file_name}:{definition_name}"
                    break
                else:
                    for child in search_node.children:
                        await search_queue.put(child)

            # If a valid entity name was found, register the entity
            if entity_name:           
                
                # Build the summary prompt
                prompt = CODE_SUMMARY_PROMPT_TEMPLATE.format(node_text=node_text)

                # Run code summary generation
                description = await complete_graph_create(prompt=prompt)

                # Register entity
                entities.append(
                    {
                        "entity_name": entity_name,
                        "entity_type": current_node.type,
                        "description": description,
                        "source_id": source_id,
                        "file_path": code_path
                    }
                )

                # Create parent-child relationship
                if parent_definition_name and f"{file_name}:{parent_definition_name}" != entity_name:
                    relationships.append({
                        "src_id": f"{file_name}:{parent_definition_name}",
                        "tgt_id": entity_name,
                        "description": f"The {definition_name} of {parent_definition_name} located in lines {start_line} through {end_line}.",
                        "keywords": f"{parent_definition_name} {definition_name}",
                        "weight": 1.0,
                        "source_id": source_id,
                        "file_path": code_path
                    })

        # Traverse children if depth is below configured maximum
        if depth < max_depth:
            for child_node in current_node.children:
                await task_queue.put((child_node, definition_name, depth + 1))

    # Return the generated lists
    return entities, relationships
