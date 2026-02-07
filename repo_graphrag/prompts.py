# ========================================
# Prompt for plan creation
# ========================================

PLAN_PROMPT_TEMPLATE = """
# Role
You are an excellent manager who creates an implementation plan from a modification request.
Create an accurate and error-free plan assuming that other LLMs/agents will execute the plan.

# Task
Rewrite the modification request into an "implementation plan" to be handed off to other LLMs/agents.
Include the following steps in the plan:
- Preparation
    1. Identify file paths of code to be newly created or modified
    2. Identify file paths of documents to be newly created or modified
    3. Investigate dependencies and impact range
- Design
- Implementation
    1. Create/modify documents
    2. Create/modify code

# Rules
Always include the following:
- Always include the paths of target documents and code files to be modified.
- Documents and code are a set. If either documents or code is newly created or modified, update both to avoid inconsistencies.
- Perform the minimum changes necessary to fulfill the requested requirements.

# Modification Request:
{user_request}
"""

# ========================================
# Prompt for code summarization
# ========================================

CODE_SUMMARY_PROMPT_TEMPLATE = """# Instructions
Extract the important elements and processes from the program and create a brief summary statement described in natural language.

# Rules
- Create a summary statement using natural language, not the program.
- Output only a pure summary without any supplements or questions.

# Program
{node_text}

# Summary statement"""


# ========================================
# Response message templates
# ========================================

PLAN_RESPONSE_TEMPLATE = """
# Task
An implementation plan has been created by referencing the storage based on the modification request.
Present the plan content to the user in an easy-to-understand manner, and ask for their decision on whether to autonomously execute document and code updates based on this plan.
If there are ambiguous or unclear parts in the plan, refer to the sample questions and call the tool "graph_query" to ask questions.

Modification Request:
{user_request}

Implementation Plan:
{plan}

# Sample Questions
- graph: Tell me what the function does {storage_name}
- graph: I want to know the class names in the file {storage_name}
- {storage_name} Please explain the processing flow of the following part graph:
    
# Note
In the following cases, the storage referenced for planning may not include the current implementation and may be outdated.
Only if applicable, inform the user that the storage may be outdated and recommend updating the storage.
- If the plan mentions that the storage differs from the state the user expects as current.
"""

QUERY_RESPONSE_TEMPLATE = """
# Task
An answer has been created by referencing the storage for the user's question.
If there are ambiguous or unclear parts in the answer, refer to the sample questions and call the tool "graph_query" to ask questions.
If the answer states that it cannot respond precisely to the question, do not ask follow-up questions.

Question:
{user_query}

Answer:
{response}

# Sample Questions
- graph: Tell me what the function does {storage_name}
- graph: I want to know the class names in the file {storage_name}
- {storage_name} Please explain the processing flow of the following part graph:

# Note
In the following cases, the storage referenced for the answer may not include the current implementation and may be outdated.
Only if applicable, inform the user that the storage may be outdated and recommend updating the storage.
- If the answer mentions that the storage differs from the state the user expects as current.
"""

GRAPH_STORAGE_RESULT_TEMPLATE = """
GraphRAG storage {action} completed.

Result:
- Read directory: {read_dir_path}
- {action} storage: {storage_dir_path}
"""

# ========================================
# Error message templates
# ========================================

STORAGE_NOT_FOUND_ERROR_TEMPLATE = "Error: GraphRAG storage not found.\nStorage name: {storage_name}"

GENERAL_ERROR_TEMPLATE = "An error occurred: {error}"
