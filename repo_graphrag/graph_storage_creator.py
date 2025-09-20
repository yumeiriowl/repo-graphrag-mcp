import gc
import logging
import os
import json
from lightrag import LightRAG
from lightrag.utils import compute_mdhash_id
from .initialization.initializer import initialize_rag
from .utils.file_reader import read_dir
from .processors.document_processor import doc_to_storage
from .processors.code_processor import code_to_storage
from .processors.entity_merger import merge_doc_and_code
from .config.settings import merge_enabled


logger = logging.getLogger(__name__)

async def create_graph_storage(read_dir_path: str, storage_dir_path: str):
    """
    Create or update GraphRAG storage.

    Args:
        read_dir_path: Target directory path to read from
        storage_dir_path: Storage directory path
    """
    rag = None
    try:
        # Initialize LightRAG
        rag = await initialize_rag(storage_dir_path)

        # Get workspace path
        storage_name = os.path.basename(storage_dir_path.rstrip('/'))
        workspace_dir_path = os.path.join(storage_dir_path, storage_name + "_work")

        # Extract document and code files from the given directory
        doc_dict, code_dict = read_dir(read_dir_path)

        # If storage exists, delete stale/out-of-scope entries and identify files to process this run
        current_process_doc_dict, current_process_code_dict = await _cleanup_and_prepare_documents(
            rag,
            workspace_dir_path,
            doc_dict,
            code_dict,
            read_dir_path
        )

        # Chunk and graph documents (only the files to be processed this run)
        await doc_to_storage(rag, current_process_doc_dict)

        # Chunk and graph code (only the files to be processed this run)
        await code_to_storage(rag, current_process_code_dict)

        # Merge document and code entities (only when enabled by settings)
        if merge_enabled:
            await merge_doc_and_code(rag, current_process_code_dict)
        else:
            logger.info("MERGE_ENABLED=false, skipping entity merge")
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
    finally:
        if rag:
            await rag.finalize_storages()
            
            # Drop caches
            await rag.llm_response_cache.drop()
            
            # Delete instance
            del rag
            
            # Attempt global GC
            gc.collect()

async def _cleanup_and_prepare_documents(
    rag: LightRAG, 
    workspace_dir_path: str, 
    doc_dict: dict, 
    code_dict: dict, 
    read_dir_path: str = None
)-> tuple[dict, dict]:
    """
    Delete stale/out-of-scope files from storage and determine the set of files to process in this run.

    Args:
        rag: LightRAG instance
        workspace_dir_path: Workspace directory path
        doc_dict: Current document file dictionary
        code_dict: Current code file dictionary
        read_dir_path: Target directory path to read from

    Returns:
        tuple: (document_dict_to_process, code_dict_to_process)
    """
    try:
        # Build path to kv_store_text_chunks.json
        text_chunks_path = os.path.join(workspace_dir_path, "kv_store_text_chunks.json")
        
        # If the file doesn't exist, treat as a new storage; process all files
        if not os.path.exists(text_chunks_path):
            return doc_dict, code_dict
        
        # Load existing storage chunk metadata
        with open(text_chunks_path, "r", encoding="utf-8") as f:
            storage_chunks_json = json.load(f)
        
        # Build a map of current file paths to document IDs
        current_doc_dict = {}
        
        # Generate IDs for document files (clean content same as LightRAG)
        for doc_file_path, doc_content in doc_dict.items():
            cleaned_content = doc_content.replace('\x00', '').strip() if doc_content else ""
            current_doc_dict[doc_file_path] = compute_mdhash_id(cleaned_content, prefix="doc-")
        
        # Generate IDs for code files (no normalization)
        for code_file_path, code_content_bytes in code_dict.items():
            code_content = code_content_bytes.decode('utf-8')
            current_doc_dict[code_file_path] = compute_mdhash_id(code_content, prefix="doc-")
        
        # Determine document IDs to delete and the set of files to process this run
        docs_to_delete = set()
        out_of_scope_docs = set()  # out-of-scope files
        unchanged_files = set()    # unchanged files
        
        for _, storage_chunk_data in storage_chunks_json.items():       
            storage_chunk_file_path = storage_chunk_data["file_path"]
            storage_chunk_full_doc_id = storage_chunk_data["full_doc_id"]
            
            # Files outside the target directory are treated as out-of-scope and deleted
            if read_dir_path and not storage_chunk_file_path.startswith(read_dir_path):
                out_of_scope_docs.add(storage_chunk_full_doc_id)
                continue
            
            # Within the target directory, if both file path and doc ID match, skip updating
            if storage_chunk_file_path in current_doc_dict:
                if storage_chunk_full_doc_id == current_doc_dict[storage_chunk_file_path]:
                    unchanged_files.add(storage_chunk_file_path)
                    continue
            
            # Otherwise, mark for deletion (moved/changed/deleted files)
            docs_to_delete.add(storage_chunk_full_doc_id)
        
        # Select files to process this run (exclude unchanged files)
        current_process_doc_dict = {k: v for k, v in doc_dict.items() if k not in unchanged_files}
        current_process_code_dict = {k: v for k, v in code_dict.items() if k not in unchanged_files}
        
        logger.info("=" * 50)
        logger.info(f"Documents to process this run: {len(current_process_doc_dict)}")
        logger.info(f"Code files to process this run: {len(current_process_code_dict)}")
        
        # Execute deletions (out-of-scope + changed files)
        all_docs_to_delete = docs_to_delete | out_of_scope_docs
        
        if all_docs_to_delete:
            logger.info(f"Deleting {len(all_docs_to_delete)} documents (out-of-scope: {len(out_of_scope_docs)}, changed: {len(docs_to_delete)})")
            
            for doc_id in all_docs_to_delete:
                try:
                    await rag.adelete_by_doc_id(doc_id)
                except Exception as e:
                    logger.error(f"Delete error {doc_id}: {e}")
                         
            logger.info("Completed deletion of stale documents")
        else:
            logger.info("No documents to delete")
        
        logger.info("=" * 50)
        logger.info("")
        
        return current_process_doc_dict, current_process_code_dict
            
    except Exception as e:
        logger.error(f"Error during document cleanup: {e}")
        # On error, process all files
        return doc_dict, code_dict
