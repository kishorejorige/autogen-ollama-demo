from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient


def create_manager_agent(
    model_client: OllamaChatCompletionClient,
) -> AssistantAgent:
    return AssistantAgent(
        name="manager_agent",
        model_client=model_client,
        system_message=(
            "You are the Manager Agent. "
            "Your responsibility is to understand the user's request, "
            "decide which specialist agent should perform the task, "
            "and coordinate the overall workflow."
        ),
    )
