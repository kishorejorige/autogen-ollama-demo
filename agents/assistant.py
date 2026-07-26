from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient


def create_python_assistant(
    model_client: OllamaChatCompletionClient,
) -> AssistantAgent:
    return AssistantAgent(
        name="python_assistant",
        model_client=model_client,
        system_message=(
            "You are a helpful Python development assistant. "
            "Give clear, concise, and practical answers."
        ),
    )
