from typing import List, Dict, Any
from ..config.settings import graph_create_provider, graph_analysis_provider


# Import the appropriate client for the CREATE provider
if graph_create_provider == "anthropic":
    from .anthropic_client import anthropic_complete_graph_create
    graph_create_complete = anthropic_complete_graph_create
elif graph_create_provider == "azure_openai":
    from .azure_openai_client import azure_openai_complete_graph_create
    graph_create_complete = azure_openai_complete_graph_create
elif graph_create_provider == "openai":
    from .openai_client import openai_complete_graph_create
    graph_create_complete = openai_complete_graph_create
elif graph_create_provider == "gemini":
    from .gemini_client import gemini_complete_graph_create
    graph_create_complete = gemini_complete_graph_create
else:
    raise ValueError(f"Unsupported GRAPH_CREATE_PROVIDER: {graph_create_provider}")

# Import the appropriate client for the ANALYSIS provider
if graph_analysis_provider == "anthropic":
    from .anthropic_client import anthropic_complete_graph_plan
    graph_analysis_complete = anthropic_complete_graph_plan
elif graph_analysis_provider == "azure_openai":
    from .azure_openai_client import azure_openai_complete_graph_plan
    graph_analysis_complete = azure_openai_complete_graph_plan
elif graph_analysis_provider == "openai":
    from .openai_client import openai_complete_graph_plan
    graph_analysis_complete = openai_complete_graph_plan
elif graph_analysis_provider == "gemini":
    from .gemini_client import gemini_complete_graph_plan
    graph_analysis_complete = gemini_complete_graph_plan
else:
    raise ValueError(f"Unsupported GRAPH_ANALYSIS_PROVIDER: {graph_analysis_provider}")

async def complete_graph_create(
    prompt: str,
    system_prompt: str = "",
    history_messages: List[Dict[str, Any]] = [],
    **kwargs
) -> str:
    """
    Execute the LLM using the provider configured for CREATE.

    Args:
        prompt: Prompt to execute
        system_prompt: System prompt
        history_messages: Conversation history
        **kwargs: Additional parameters

    Returns:
        str: LLM response text
    """
    return await graph_create_complete(prompt, system_prompt, history_messages, **kwargs)

async def complete_graph_plan(
    prompt: str,
    system_prompt: str = "",
    history_messages: List[Dict[str, Any]] = [],
    **kwargs
) -> str:
    """
    Execute the LLM using the provider configured for ANALYSIS.

    Args:
        prompt: Prompt to execute
        system_prompt: System prompt
        history_messages: Conversation history
        **kwargs: Additional parameters

    Returns:
        str: LLM response text
    """
    return await graph_analysis_complete(prompt, system_prompt, history_messages, **kwargs)
