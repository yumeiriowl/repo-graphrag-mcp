import gc
import os
import asyncio
from lightrag import LightRAG
from transformers import AutoModel, AutoTokenizer
from lightrag.utils import EmbeddingFunc
from lightrag.llm.hf import hf_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
from ..llm.llm_client import complete_graph_create
from ..config.settings import (
    parallel_num, 
    graph_create_max_token_size,
    embedding_model_name,
    embedding_dim, 
    embedding_max_token_size, 
    llm_model_max_async,
    embedding_func_max_async, 
    document_definition_list,
    huggingface_hub_token
)


_emb_model = None
_tokenizer = None
_embed_init_lock = None

async def _load_embedding_components() -> None:
    """
    Initialize and cache the embedding model and tokenizer (thread-safe once-only init).
    """
    global _emb_model, _tokenizer, _embed_init_lock

    if _emb_model is not None and _tokenizer is not None:
        return

    # Share the same lock across calls
    lock = _embed_init_lock
    if lock is None:
        new_lock = asyncio.Lock()
        if _embed_init_lock is None:
            _embed_init_lock = new_lock
            lock = new_lock
        else:
            lock = _embed_init_lock

    async with lock:
        if _emb_model is not None and _tokenizer is not None:
            return
        # Load embedding model & tokenizer (optionally with HF auth token if provided)
        if huggingface_hub_token:
            _emb_model = await asyncio.to_thread(AutoModel.from_pretrained, embedding_model_name, token=huggingface_hub_token)
            _tokenizer = await asyncio.to_thread(AutoTokenizer.from_pretrained, embedding_model_name, token=huggingface_hub_token)
        else:
            _emb_model = await asyncio.to_thread(AutoModel.from_pretrained, embedding_model_name)
            _tokenizer = await asyncio.to_thread(AutoTokenizer.from_pretrained, embedding_model_name)

async def initialize_rag(storage_dir_path: str) -> LightRAG:
    """
    Initialize and return a configured LightRAG instance.
    
    Args:
        storage_dir_path: Path to the storage directory
    
    Returns:
        LightRAG: The initialized LightRAG instance
    """
    
    # Attempt to clean up global state
    gc.collect()
    
    # Derive storage name from path
    storage_name = os.path.basename(storage_dir_path.rstrip('/'))
    
    # Ensure embedding model and tokenizer are loaded
    await _load_embedding_components()

    # Construct LightRAG with configured parameters
    rag = LightRAG(
        working_dir=storage_dir_path,  # storage path
        workspace=storage_name+"_work",  # workspace name
        max_parallel_insert=parallel_num,  # parallelism for chunking/graphing
        vector_storage="FaissVectorDBStorage",  # use Faiss for vectors
        llm_model_func=complete_graph_create,  # LLM for entity extraction/summaries
        summary_max_tokens=graph_create_max_token_size,  # max tokens for graph_create
        embedding_func=EmbeddingFunc(  # embedding function
            embedding_dim=embedding_dim,  # embedding dimension
            max_token_size=embedding_max_token_size,  # max tokens for embedding model
            func=lambda texts: hf_embed(  # vectorize texts via HF model
                texts,
                tokenizer=_tokenizer,
                embed_model=_emb_model,
            )
        ),
        llm_model_max_async=llm_model_max_async,  # LLM concurrency limit
        embedding_func_max_async=embedding_func_max_async,  # embed concurrency limit
        addon_params={
            "language": "english",  # language for summaries
            "entity_types": document_definition_list,  # entity types to extract from docs
        }
    )

    # Initialize storages and pipeline status
    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag

def get_tokenizer() -> AutoTokenizer:
    """
    Get the tokenizer used by the embedding model.
    
    Returns:
        AutoTokenizer: Tokenizer for the embedding model
    """
    return _tokenizer
