from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient


def create_manager_agent(
    model_client: OllamaChatCompletionClient,
) -> AssistantAgent:
    return AssistantAgent(
        name="manager_agent",
        model_client=model_client,
        system_message=(
            "You are the Manager Agent of an AI software team.\n\n"
            "Responsibilities:\n"
            "1. Understand the user's request.\n"
            "2. Decide which specialist should handle it.\n"
            "3. Explain your decision briefly.\n"
            "4. DO NOT solve programming tasks yourself.\n"
            "5. Leave implementation to the specialist agent."
        ),
    )
