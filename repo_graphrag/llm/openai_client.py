from ..config.settings import (
    graph_create_model_name, 
    graph_analysis_model_name, 
    graph_create_max_token_size,
    graph_analysis_max_token_size,
    openai_api_key,
    rate_limit_error_wait_time
)
from ..utils.rate_limiter import get_rate_limiter
from typing import List, Dict, Any
from openai import AsyncOpenAI
import asyncio
import logging


logger = logging.getLogger(__name__)

# Initialize OpenAI client
_openai_client = None
if openai_api_key:
    _openai_client = AsyncOpenAI(
        api_key=openai_api_key,
        timeout=300.0
    )

async def openai_complete_graph_create(
    prompt: str,
    system_prompt: str = "",
    history_messages: List[Dict[str, Any]] = [],
    **kwargs
) -> str:
    """
    Execute a prompt with OpenAI LLM (graph_create use-case).

    Args:
        prompt: Prompt to execute
        system_prompt: System prompt
        history_messages: Conversation history
        **kwargs: Additional parameters

    Returns:
        str: LLM response text
    """
    if not _openai_client:
        raise ValueError("OpenAI API key is not configured")
    
    # Prepare conversation messages
    messages = []

    # If provided, add system prompt first
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    # Append history messages
    messages.extend(history_messages)

    # Append user prompt
    messages.append({
        "role": "user",
        "content": prompt
    })

    # Set max token size
    max_tokens = kwargs.get('max_tokens', graph_create_max_token_size)

    # Apply rate limiting and call LLM
    async with get_rate_limiter():
        try:
            # Call LLM
            response = await _openai_client.chat.completions.create(
                model=graph_create_model_name,
                messages=messages,
                max_completion_tokens=max_tokens
            )
        except Exception as e:
            logger.error(f"OpenAI API Error (graph_create): {e}")
            if "rate" in str(e).lower():
                logger.warning("Rate limit detected, waiting...")
                await asyncio.sleep(rate_limit_error_wait_time)
            raise

    # Return response
    return response.choices[0].message.content

async def openai_complete_graph_plan(
    prompt: str,
    system_prompt: str = "",
    history_messages: List[Dict[str, Any]] = [],
    **kwargs
) -> str:
    """
    Execute a prompt with OpenAI LLM (graph_plan use-case).

    Args:
        prompt: Prompt to execute
        system_prompt: System prompt
        history_messages: Conversation history
        **kwargs: Additional parameters

    Returns:
        str: LLM response text
    """
    if not _openai_client:
        raise ValueError("OpenAI API key is not configured")
    
    # Prepare conversation messages
    messages = []

    # If provided, add system prompt first
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    # Append history messages
    messages.extend(history_messages)

    # Append user prompt
    messages.append({
        "role": "user",
        "content": prompt
    })

    # Set max token size
    max_tokens = kwargs.get('max_tokens', graph_analysis_max_token_size)

    # Apply rate limiting and call LLM
    async with get_rate_limiter():
        try:
            # Call LLM
            response = await _openai_client.chat.completions.create(
                model=graph_analysis_model_name,
                messages=messages,
                max_completion_tokens=max_tokens
            )
        except Exception as e:
            logger.error(f"OpenAI API Error (graph_plan): {e}")
            if "rate" in str(e).lower():
                logger.warning("Rate limit detected, waiting...")
                await asyncio.sleep(rate_limit_error_wait_time)
            raise

    # Return response
    return response.choices[0].message.content