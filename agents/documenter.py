from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient

DOCUMENTER_SYSTEM_PROMPT = """You are a Technical Writer & Documentation Specialist.

Hard Rules:
1. Acknowledge the Requirements Validator status, Code Reviewer status, and Tester status.
2. NEVER upgrade a NEEDS_ATTENTION or FAIL status to COMPLETE.
3. NEVER call rejected, incomplete, or unverified code "production-ready".
4. Clearly distinguish implemented items from planned recommendations or missing items.
5. Provide honest documentation summarizing what was actually generated and tested.
"""


def create_documentation_agent(
    model_client: OllamaChatCompletionClient,
) -> AssistantAgent:
    return AssistantAgent(
        name="documentation_agent",
        model_client=model_client,
        system_message=DOCUMENTER_SYSTEM_PROMPT,
    )
