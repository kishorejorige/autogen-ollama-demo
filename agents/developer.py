from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient


def create_python_developer_agent(
    model_client: OllamaChatCompletionClient,
) -> AssistantAgent:
    return AssistantAgent(
        name="python_developer",
        model_client=model_client,
        system_message=(
            "You are a senior Python developer. "
            "Write clean, readable, and well-documented Python code. "
            "Follow Python best practices, explain your reasoning when helpful, "
            "and prefer simple, maintainable solutions."
        ),
    )
