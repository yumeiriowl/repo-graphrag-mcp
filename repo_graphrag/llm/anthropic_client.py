from ..config.settings import (
    graph_create_model_name, 
    graph_analysis_model_name, 
    graph_create_max_token_size,
    graph_analysis_max_token_size,
    anthropic_api_key,
    rate_limit_error_wait_time
)
from ..utils.rate_limiter import get_rate_limiter
from typing import List, Dict, Any
import anthropic
import asyncio
import logging


logger = logging.getLogger(__name__)

# Initialize Anthropic client
_anthropic_client = None
if anthropic_api_key:
    _anthropic_client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)

async def anthropic_complete_graph_create(
    prompt: str,
    system_prompt: str = "",
    history_messages: List[Dict[str, Any]] = [],
    **kwargs
) -> str:
    """
    Execute a prompt with Anthropic LLM (graph_create use-case).

    Args:
        prompt: Prompt to execute
        system_prompt: System prompt
        history_messages: Conversation history
        **kwargs: Additional parameters

    Returns:
        str: LLM response text
    """
    if not _anthropic_client:
        raise ValueError("Anthropic API key is not configured")
    
    # Prepare messages
    messages = []
    messages.extend(history_messages)

    # Append user prompt to messages
    messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # Set max token size
    max_tokens = kwargs.get('max_tokens', graph_create_max_token_size)

    # Apply rate limiting and run LLM
    async with get_rate_limiter():
        try:
            # Execute LLM
            response = await _anthropic_client.messages.create(
                system=system_prompt,
                model=graph_create_model_name,
                max_tokens=max_tokens,
                messages=messages,
            )
        except anthropic.RateLimitError as e:
            logger.warning(f"Anthropic Rate Limit Error (graph_create): {e}")
            await asyncio.sleep(rate_limit_error_wait_time)
            raise
        except Exception as e:
            logger.error(f"Anthropic API Error (graph_create): {e}")
            raise

    # Return response
    return response.content[0].text

async def anthropic_complete_graph_plan(
    prompt: str,
    system_prompt: str = "",
    history_messages: List[Dict[str, Any]] = [],
    **kwargs
) -> str:
    """
    Execute a prompt with Anthropic LLM (graph_plan use-case).

    Args:
        prompt: Prompt to execute
        system_prompt: System prompt
        history_messages: Conversation history
        **kwargs: Additional parameters

    Returns:
        str: LLM response text
    """
    if not _anthropic_client:
        raise ValueError("Anthropic API key is not configured")
    
    # Prepare messages
    messages = []
    messages.extend(history_messages)

    # Append user prompt to messages
    messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # Set max token size
    max_tokens = kwargs.get('max_tokens', graph_analysis_max_token_size)

    # Apply rate limiting and run LLM
    async with get_rate_limiter():
        try:
            # Execute LLM
            response = await _anthropic_client.messages.create(
                system=system_prompt,
                model=graph_analysis_model_name,
                max_tokens=max_tokens,
                messages=messages,
            )
        except anthropic.RateLimitError as e:
            logger.warning(f"Anthropic Rate Limit Error (graph_plan): {e}")
            await asyncio.sleep(rate_limit_error_wait_time)
            raise
        except Exception as e:
            logger.error(f"Anthropic API Error (graph_plan): {e}")
            raise

    # Return response
    return response.content[0].text
