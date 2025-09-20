from ..config.settings import (
    graph_create_model_name, 
    graph_analysis_model_name, 
    graph_create_max_token_size,
    graph_analysis_max_token_size,
    azure_openai_api_key,
    azure_endpoint,
    azure_api_version,
    rate_limit_error_wait_time
)
from ..utils.rate_limiter import get_rate_limiter
from typing import List, Dict, Any
from openai import AsyncAzureOpenAI
import asyncio
import logging


logger = logging.getLogger(__name__)

# Initialize Azure OpenAI client
_azure_openai_client = None
if azure_openai_api_key:
    _azure_openai_client = AsyncAzureOpenAI(
        api_key=azure_openai_api_key,
        api_version=azure_api_version,
        azure_endpoint=azure_endpoint
    )

async def azure_openai_complete_graph_create(
    prompt: str,
    system_prompt: str = "",
    history_messages: List[Dict[str, Any]] = [],
    **kwargs
) -> str:
    """
    Execute a prompt with Azure OpenAI LLM (graph_create use-case).

    Args:
        prompt: Prompt to execute
        system_prompt: System prompt
        history_messages: Conversation history
        **kwargs: Additional parameters

    Returns:
        str: LLM response text
    """
    if not _azure_openai_client:
        raise ValueError("Azure OpenAI API key is not configured")
    
    # Prepare messages
    messages = []

    # Add system prompt first when provided
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    # Add history messages
    messages.extend(history_messages)

    # Append user prompt to messages
    messages.append({
        "role": "user",
        "content": prompt
    })

    # Set max token size
    max_tokens = kwargs.get('max_tokens', graph_create_max_token_size)

    # Apply rate limiting and run LLM
    async with get_rate_limiter():
        try:
            # Execute LLM
            response = await _azure_openai_client.chat.completions.create(
                model=graph_create_model_name,
                messages=messages,
                max_tokens=max_tokens
            )
        except Exception as e:
            logger.error(f"Azure OpenAI API Error (graph_create): {e}")
            if "rate" in str(e).lower():
                logger.warning("Rate limit detected, waiting...")
                await asyncio.sleep(rate_limit_error_wait_time)
            raise

    # Return response
    return response.choices[0].message.content

async def azure_openai_complete_graph_plan(
    prompt: str,
    system_prompt: str = "",
    history_messages: List[Dict[str, Any]] = [],
    **kwargs
) -> str:
    """
    Execute a prompt with Azure OpenAI LLM (graph_plan use-case).
    
    Args:
        prompt: Prompt to execute
        system_prompt: System prompt
        history_messages: Conversation history
        **kwargs: Additional parameters
    
    Returns:
        str: LLM response text
    """
    if not _azure_openai_client:
        raise ValueError("Azure OpenAI API key is not configured")
    
    # Prepare messages
    messages = []

    # Add system prompt first when provided
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    # Add history messages
    messages.extend(history_messages)

    # Append user prompt to messages
    messages.append({
        "role": "user",
        "content": prompt
    })

    # Set max token size
    max_tokens = kwargs.get('max_tokens', graph_analysis_max_token_size)

    # Apply rate limiting and run LLM
    async with get_rate_limiter():
        try:
            # Execute LLM
            response = await _azure_openai_client.chat.completions.create(
                model=graph_analysis_model_name,
                messages=messages,
                max_tokens=max_tokens
            )
        except Exception as e:
            logger.error(f"Azure OpenAI API Error (graph_plan): {e}")
            if "rate" in str(e).lower():
                logger.warning("Rate limit detected, waiting...")
                await asyncio.sleep(rate_limit_error_wait_time)
            raise

    # Return response
    return response.choices[0].message.content
