from ..config.settings import (
    graph_create_model_name, 
    graph_analysis_model_name, 
    graph_create_max_token_size,
    graph_analysis_max_token_size,
    gemini_api_key,
    rate_limit_error_wait_time
)
from ..utils.rate_limiter import get_rate_limiter
from typing import List, Dict, Any
from google import genai
from google.genai import types
import asyncio
import logging


logger = logging.getLogger(__name__)

# Initialize Gemini client
gemini_client = None
if gemini_api_key:
    gemini_client = genai.Client(api_key=gemini_api_key)

async def gemini_complete_graph_create(
    prompt: str,
    system_prompt: str = "",
    history_messages: List[Dict[str, Any]] = [],
    **kwargs
) -> str:
    """
    Execute a prompt with Gemini LLM (graph_create use-case).

    Args:
        prompt: Prompt to execute
        system_prompt: System prompt
        history_messages: Conversation history
        **kwargs: Additional parameters

    Returns:
        str: LLM response text
    """
    if not gemini_client:
        raise ValueError("Gemini API key is not configured")
    
    # Set max token size
    max_tokens = kwargs.get('max_tokens', graph_create_max_token_size)
    
    try:
    # Use ChatSession when history exists
        if history_messages:
            # Convert history to Content objects
            history_content = []
            for msg in history_messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    if role == "assistant":
                        role = "model"
                    content_obj = types.Content(
                        role=role,
                        parts=[types.Part(text=content)]
                    )
                    history_content.append(content_obj)
            
            # Prepare ChatSession
            chat = gemini_client.chats.create(
                model=graph_create_model_name,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt if system_prompt else None,
                    max_output_tokens=max_tokens
                ),
                history=history_content
            )
            
            # Apply rate limiting and run LLM
            async with get_rate_limiter():
                response = await asyncio.to_thread(
                    chat.send_message,
                    prompt
                )
        else:
            # If no history, send a single request
            async with get_rate_limiter():
                response = await asyncio.to_thread(
                    gemini_client.models.generate_content,
                    model=graph_create_model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt if system_prompt else None,
                        max_output_tokens=max_tokens
                    )
                )
    except Exception as e:
        logger.error(f"Gemini API Error (graph_create): {e}")
        if "quota" in str(e).lower() or "rate" in str(e).lower():
            logger.warning("Rate limit detected, waiting...")
            await asyncio.sleep(rate_limit_error_wait_time)
        raise

    # Return response
    return response.text

async def gemini_complete_graph_plan(
    prompt: str,
    system_prompt: str = "",
    history_messages: List[Dict[str, Any]] = [],
    **kwargs
) -> str:
    """
    Execute a prompt with Gemini LLM (graph_plan use-case).

    Args:
        prompt: Prompt to execute
        system_prompt: System prompt
        history_messages: Conversation history
        **kwargs: Additional parameters

    Returns:
        str: LLM response text
    """
    if not gemini_client:
        raise ValueError("Gemini API key is not configured")
    
    # Set max token size
    max_tokens = kwargs.get('max_tokens', graph_analysis_max_token_size)
    
    try:
    # Use ChatSession when history exists
        if history_messages:
            # Convert history to Content objects
            history_content = []
            for msg in history_messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    if role == "assistant":
                        role = "model"
                    content_obj = types.Content(
                        role=role,
                        parts=[types.Part(text=content)]
                    )
                    history_content.append(content_obj)
            
            # Prepare ChatSession
            chat = gemini_client.chats.create(
                model=graph_analysis_model_name,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt if system_prompt else None,
                    max_output_tokens=max_tokens
                ),
                history=history_content
            )
            
            # Apply rate limiting and run LLM
            async with get_rate_limiter():
                response = await asyncio.to_thread(
                    chat.send_message,
                    prompt
                )
        else:
            # If no history, send a single request
            async with get_rate_limiter():
                response = await asyncio.to_thread(
                    gemini_client.models.generate_content,
                    model=graph_analysis_model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt if system_prompt else None,
                        max_output_tokens=max_tokens
                    )
                )
    except Exception as e:
        logger.error(f"Gemini API Error (graph_plan): {e}")
        if "quota" in str(e).lower() or "rate" in str(e).lower():
            logger.warning("Rate limit detected, waiting...")
            await asyncio.sleep(rate_limit_error_wait_time)
        raise

    # Return response
    return response.text
