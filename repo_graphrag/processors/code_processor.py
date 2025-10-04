import os
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any
from tree_sitter import Parser
from lightrag import LightRAG
from lightrag.utils import compute_mdhash_id
from lightrag.base import DocStatus
from ..config.settings import code_ext_dict, parallel_num
from .code_chunker import create_code_chunks
from .code_grapher import create_code_graph
from ..utils.node_line_range import get_node_line_range, build_line_offset_list


logger = logging.getLogger(__name__)

async def code_to_storage(rag: LightRAG, code_dict: Dict[str, bytes]) -> None:
    """
    Chunk code, build a graph, and store into backend storage.
    
    Args:
        rag: LightRAG instance
        code_dict: Mapping of file path -> file content bytes
    """
    logger.info("=" * 50)
    logger.info("Graphing code files")
    logger.info(f"Starting code processing: {len(code_dict)} files")

    # Per-file processing function (run concurrently)
    async def process_file(code_path: str, file_content_bytes: bytes) -> Dict[str, Any]:
        file_name = os.path.basename(code_path)

    # Extract extension from filename
        _, ext = os.path.splitext(file_name)

    # Prepare Tree-sitter parser
        language = code_ext_dict[ext.lstrip(".")]["language"]
        parser = Parser(language)

    # Parse bytes into syntax tree
        tree = parser.parse(file_content_bytes)

    # Get root node
        root_node = tree.root_node

    # Decode bytes to UTF-8 text
        file_content_text = file_content_bytes.decode('utf-8')

        # Build robust line offset list (handles LF / CRLF uniformly)
        line_offset_list = build_line_offset_list(file_content_bytes)

        chunks = []
        entities = []
        relationships = []

    # Extract nodes to be chunked
        chunk_node_list = await create_code_chunks(root_node, file_content_bytes)

    # Get definition node types to extract as entities
        definition_dict = code_ext_dict[ext.lstrip(".")]["definition"]

    # For each target node, perform chunking and graph extraction
        for node, node_text in chunk_node_list:
            
            # Get line range
            start_line, end_line = get_node_line_range(node, line_offset_list)

            # Set chunk ID
            source_id = f"file:{file_name}_line:{start_line}-{end_line}"

            # Append chunk with its ID
            chunks.append(
                {
                    "content": node_text,
                    "source_id": source_id,
                    "file_path": code_path
                }
            )

            # Extract graph elements (entities, relationships)
            chunk_entities, chunk_relationships = await create_code_graph(
                node=node,
                definition_dict=definition_dict,
                file_content_bytes=file_content_bytes,
                parent_definition_name="",
                source_id=source_id,
                code_path=code_path,
                line_offset_list=line_offset_list
            )

            # Append extracted entities/relationships
            entities += chunk_entities
            relationships += chunk_relationships

        logger.info(f"Done: {code_path}")
        # Return file/chunks/graph information
        return {
            "file_path": code_path,
            "file_content": file_content_text,
            "chunks": chunks,
            "entities": entities,
            "relationships": relationships
        }

    file_item_list = list(code_dict.items())

    # Set batch size for concurrent processing
    batch_size = parallel_num
    total_batches = len(file_item_list) // batch_size + (1 if len(file_item_list) % batch_size > 0 else 0)

    # Run batched processing
    for batch_index in range(0, len(file_item_list), batch_size):
        batch_item_list = file_item_list[batch_index:batch_index+batch_size]
        current_batch = batch_index // batch_size + 1

        logger.info(f"Processing batch {current_batch}/{total_batches}: {len(batch_item_list)} files")

        # Create per-file tasks for this batch
        batch_task_list = []
        for code_path, file_content_bytes in batch_item_list:
            task = asyncio.create_task(process_file(code_path, file_content_bytes))
            batch_task_list.append(task)

        # Execute batch tasks and collect results
        batch_results = await asyncio.gather(*batch_task_list)

        # Store each file's results into storage
        for result in batch_results:
            file_path = result["file_path"]
            file_content = result["file_content"]
            file_chunks = result["chunks"]
            file_entities = result["entities"]
            file_relationships = result["relationships"]
            
            if file_chunks or file_entities or file_relationships:
                try:
                    # Create document ID from file content
                    doc_id = compute_mdhash_id(file_content, prefix="doc-")
                    
                    logger.info(f"Saving {file_path} to storage: chunks={len(file_chunks)}, entities={len(file_entities)}, relationships={len(file_relationships)}")
                    await rag.ainsert_custom_kg(
                        custom_kg={
                            "chunks": file_chunks,
                            "entities": file_entities,
                            "relationships": file_relationships
                        },
                        full_doc_id=doc_id
                    )
                    
                    # Update document status
                    if file_chunks:
                        # Build list of chunk IDs
                        chunk_ids = [compute_mdhash_id(chunk["content"], prefix="chunk-") for chunk in file_chunks]
                        
                        # Upsert document status
                        current_time = datetime.now(timezone.utc).isoformat()
                        await rag.doc_status.upsert({
                            doc_id: {
                                "status": DocStatus.PROCESSED,
                                "chunks_count": len(file_chunks),
                                "content": file_content,
                                "content_summary": f"Code file: {os.path.basename(file_path)}",
                                "content_length": len(file_content),
                                "created_at": current_time,
                                "updated_at": current_time,
                                "file_path": file_path,
                                "chunks_list": chunk_ids,
                                "metadata": {
                                    "file_type": "code", 
                                    "processed_by": 
                                    "code_processor"
                                }
                            }
                        })
                        
                        # Save to full document storage
                        await rag.full_docs.upsert(
                            {
                                doc_id: {"content": file_content}
                            }
                        )
                        
                        logger.info(f"Updated doc status for {file_path} (chunks_list: {len(chunk_ids)})")
                    
                    logger.info(f"Saved {file_path} to storage (ID: {doc_id})")
                except Exception as e:
                    logger.error(f"code_processor error for {file_path}: {e}")
                    raise
        
        # Add short delay between batches except after the last one
        if current_batch < total_batches:
            logger.info("Waiting 2 seconds before next batch...")
            await asyncio.sleep(2.0)

    logger.info("All code processing completed")
    logger.info("=" * 50 + "\n")
