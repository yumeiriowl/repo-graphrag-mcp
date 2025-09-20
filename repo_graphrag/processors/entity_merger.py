import asyncio
import logging
import re
import fnmatch
import numpy as np
import faiss
from typing import Optional, Dict, Any, List, Tuple
from lightrag import LightRAG
from ..config.settings import (
    parallel_num, 
    merge_score_threshold,
    merge_exclude_custom_patterns, 
    merge_exclude_private_entities_enabled,
    merge_min_name_length, 
    merge_max_name_length,
    magic_methods_exclude_list, 
    generic_terms_exclude_list, 
    test_related_exclude_list
)


logger = logging.getLogger(__name__)

def should_exclude_entity(entity_name: str) -> bool:
    """
    Determine whether an entity should be excluded from merging.
    
    Args:
        entity_name: Entity name
        
    Returns:
        bool: True if excluded
    """
    # Normalize name (lowercase, strip whitespace)
    normalized_name = entity_name.strip().lower()
    
    # Exclude empty and overly short/long names
    if (len(normalized_name) > merge_max_name_length or 
        len(normalized_name) < merge_min_name_length):
        return True
    
    # Strip file prefix if present (file:definition)
    actual_name = normalized_name.split(':', 1)[1].strip() if ':' in normalized_name else normalized_name
    
    # Custom pattern checks
    if _is_excluded_by_custom_patterns(actual_name):
        return True
    
    # Built-in pattern checks
    if _is_excluded_by_builtin_patterns(actual_name):
        return True
    
    # Special-case checks
    if _is_excluded_by_special_patterns(actual_name):
        return True
    
    return False

def _is_excluded_by_custom_patterns(actual_name: str) -> bool:
    """Check custom exclusion patterns."""
    for pattern in merge_exclude_custom_patterns:
        # Check wildcard/exact match
        if '*' in pattern or '?' in pattern:
            if fnmatch.fnmatch(actual_name, pattern.lower()):
                return True
        else:
            if actual_name == pattern.lower():
                return True
    return False

def _is_excluded_by_builtin_patterns(actual_name: str) -> bool:
    """Check built-in exclusion patterns."""
    # Magic methods
    for pattern in magic_methods_exclude_list:
        if actual_name == pattern.lower():
            return True
    
    # Generic terms
    for pattern in generic_terms_exclude_list:
        if actual_name == pattern.lower():
            return True
    
    # Test-related names
    for pattern in test_related_exclude_list:
        if actual_name == pattern.lower():
            return True
    
    return False

def _is_excluded_by_special_patterns(actual_name: str) -> bool:
    """Check special patterns (private names, numeric-only, URLs, symbols)."""
    # Private names
    if merge_exclude_private_entities_enabled and actual_name.startswith('_'):
        return True
    
    # Numeric-only
    if re.match(r'^\d+$', actual_name):
        return True
    
    # URL/path-like
    if re.match(r'^https?://', actual_name) or re.match(r'^[/\\]', actual_name):
        return True
    
    # Symbols-only
    if re.match(r'^[^\w\s]+$', actual_name):
        return True
    
    return False

async def merge_doc_and_code(rag: LightRAG, current_code_dict: Optional[Dict[str, Any]] = None) -> None:
    """
    Merge entities between documents and code based on name similarity.
    
    Args:
        rag: LightRAG instance
        current_code_dict: Mapping of currently processed code files
    """
    # Build set of current code file paths (if provided)
    current_code_file_paths = set(current_code_dict.keys()) if current_code_dict else set()
    
    # Retrieve all entity names from storage
    all_entity_name = await rag.get_graph_labels()

    # Code entities for this pass
    current_code_entity_list = []  
    
    # All document entities in storage
    all_doc_entity_list = []      
        
    for entity_name in all_entity_name:
        
        # Skip excluded entities
        if should_exclude_entity(entity_name):
            continue
        
        # Retrieve entity details
        entity = await rag.chunk_entity_relation_graph.get_node(entity_name)
        entity_file_path = entity.get("file_path")
        
        # Classification flags
        is_not_merge_entity = '<SEP>' not in entity_file_path
        has_colon_format = (':' in entity_name and 
                           not entity_name.startswith(':') and 
                           not entity_name.endswith(':'))
        is_current_target = entity_file_path in current_code_file_paths
        
        # Determine current-pass code entities vs. doc entities
        if is_current_target and is_not_merge_entity and has_colon_format:
            current_code_entity_list.append((entity.get("entity_id"), entity.get("description")))
        elif not has_colon_format or not is_not_merge_entity:
            # Non-colon format or already-merged → classify as document entity
            all_doc_entity_list.append((entity.get("entity_id"), entity.get("description")))
    
    logger.info("=" * 50)
    logger.info(f"Code entities to merge: {len(current_code_entity_list)}")
    logger.info(f"Document entities to merge: {len(all_doc_entity_list)}")
    
    if not current_code_entity_list:
        logger.info("No target code entities; skipping merge")
        logger.info("=" * 50)
        return
    
    if not all_doc_entity_list:
        logger.info("No target document entities; skipping merge")
        logger.info("=" * 50)
        return
    
    # Extract definition-name suffix from code entities
    code_definition_name_list = []
    for code_entity_name, _ in current_code_entity_list:
        definition_name = code_entity_name.split(":", 1)[1]
        code_definition_name_list.append(definition_name)

    # Embed code and document entity names
    embedding_func = rag.embedding_func
        
    code_name_embedding_array = await embedding_func(code_definition_name_list)
    doc_name_embedding_array = await embedding_func([doc_name for doc_name, _ in all_doc_entity_list])
    
    # Convert to float32 NumPy arrays
    code_embeddings = np.array(code_name_embedding_array, dtype=np.float32)
    doc_embeddings = np.array(doc_name_embedding_array, dtype=np.float32)
    
    # L2-normalize vectors
    faiss.normalize_L2(code_embeddings)
    faiss.normalize_L2(doc_embeddings)
    
    # Build index of code entities and search from doc entities
    embedding_dim = code_embeddings.shape[1]
    index = faiss.IndexFlatIP(embedding_dim)
    index.add(code_embeddings)
    
    # Search for similar code entities for each document entity
    top_matches_count = min(len(current_code_entity_list), 10)
    similarities, indices = index.search(doc_embeddings, top_matches_count)
    
    # Collect high-similarity pairs
    high_similarity_pairs = []
    for doc_idx, (doc_similarities, doc_indices) in enumerate(zip(similarities, indices)):
        doc_entity_name, doc_description = all_doc_entity_list[doc_idx]
        
        similar_codes = []
        for similarity, code_idx in zip(doc_similarities, doc_indices):
            if similarity >= merge_score_threshold and code_idx < len(current_code_entity_list):
                code_entity_name, code_description = current_code_entity_list[code_idx]
                similar_codes.append((code_entity_name, code_description))
        
        if similar_codes:
            high_similarity_pairs.append((doc_entity_name, doc_description, similar_codes))
    
    # Process in batches concurrently
    batch_size = parallel_num
    total_batches = (len(high_similarity_pairs) + batch_size - 1) // batch_size
    total_merged = 0
    
    logger.info(f"Similarity search complete: identified {len(high_similarity_pairs)} high-similarity pairs")
    logger.info(f"Starting entity merge: total batches {total_batches}")
    
    # Execute batch processing
    for batch_index in range(0, len(high_similarity_pairs), batch_size):
        batch_pairs = high_similarity_pairs[batch_index:batch_index+batch_size]
        current_batch = (batch_index // batch_size) + 1
        
        logger.info(f"Processing batch {current_batch}/{total_batches}: {len(batch_pairs)} pairs")

        # Build and run tasks for this batch
        batch_task_list = []
        for doc_entity_name, doc_description, similar_codes in batch_pairs:
            task = asyncio.create_task(
                _process_doc_entity(
                    doc_entity_name, 
                    doc_description, 
                    similar_codes
                )
            )
            batch_task_list.append(task)

        batch_results = await asyncio.gather(*batch_task_list)
        
        # Execute merge operations sequentially within the batch
        batch_merged_count = 0
        for merge_op in batch_results:
            if merge_op is None:
                continue
                
            try:
                if await _execute_merge(rag, merge_op):
                    batch_merged_count += 1
                    total_merged += 1
            except Exception as e:
                logger.error(f"entity_merger error: {e}")
                raise
        
        logger.info(f"Batch {current_batch}/{total_batches} complete: merged {batch_merged_count} (total: {total_merged})")

    logger.info(f"Entity merge complete: total merges {total_merged}")
    logger.info("=" * 50)

async def _process_doc_entity(
    doc_entity_name: str, 
    doc_description: str, 
    similar_codes: List[Tuple[str, str]]
) -> Optional[Dict[str, Any]]:
    """Build merge operation for a document entity with similar code entities."""
    if not similar_codes:
        return None
    
    # Build merged description (append code entities info)
    merge_description = f"\n{doc_description}"
    for code_entity_name, code_description in similar_codes:
        # Append "file:description" entries
        code_file_name = code_entity_name.split(":", 1)[0]
        merge_description += f"<SEP>{code_file_name}:{code_description}"
    
    return {
        "source_entities": [
            doc_entity_name,
            *[code_name for code_name, _ in similar_codes]
        ],
        "target_entity": doc_entity_name,
        "target_entity_data": {
            "description": merge_description
        },
        "doc_entity_name": doc_entity_name,
        "code_entity_names": [code_name for code_name, _ in similar_codes]
    }

async def _execute_merge(rag: LightRAG, merge_op: Dict[str, Any]) -> bool:
    """Execute a single merge operation."""
    # Filter to existing entities only
    valid_entities = []
    for entity_name in merge_op["source_entities"]:
        if await rag.chunk_entity_relation_graph.has_node(entity_name):
            valid_entities.append(entity_name)
    
    if len(valid_entities) <= 1:
        return False
    
    # Build file paths in the order used in description
    ordered_file_paths = []
    
    # Start with document entity file paths
    doc_entity = await rag.chunk_entity_relation_graph.get_node(merge_op["doc_entity_name"])
    if doc_entity and doc_entity.get("file_path"):
        doc_file_path = doc_entity.get("file_path")
        if "<SEP>" in doc_file_path:
            ordered_file_paths.extend(doc_file_path.split("<SEP>"))
        else:
            ordered_file_paths.append(doc_file_path)
    
    # Then add code entity file paths in the same order
    for code_entity_name in merge_op["code_entity_names"]:
        if await rag.chunk_entity_relation_graph.has_node(code_entity_name):
            code_entity = await rag.chunk_entity_relation_graph.get_node(code_entity_name)
            if code_entity and code_entity.get("file_path"):
                code_file_path = code_entity.get("file_path")
                ordered_file_paths.append(code_file_path)
    
    if ordered_file_paths:
        merge_op["target_entity_data"]["file_path"] = "<SEP>".join(ordered_file_paths)
    
    # Execute merge
    await rag.amerge_entities(
        source_entities=valid_entities,
        target_entity=merge_op["target_entity"],
        target_entity_data=merge_op["target_entity_data"]
    )
    
    await asyncio.sleep(0.5)
    return True
