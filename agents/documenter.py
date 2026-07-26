from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient


def create_documentation_agent(
    model_client: OllamaChatCompletionClient,
) -> AssistantAgent:
    return AssistantAgent(
        name="documentation_agent",
        model_client=model_client,
        system_message=(
            "You are a technical writer and documentation specialist.\n\n"
            "Responsibilities:\n"
            "1. Produce concise documentation, usage instructions, summaries, and README-ready content for the code.\n"
            "2. Do not modify implementation code directly.\n"
            "3. You must acknowledge the review status (APPROVED or CHANGES_REQUIRED) from the Code Reviewer's feedback.\n"
            "4. If the status is CHANGES_REQUIRED, you must not describe the rejected code as production-ready."
        ),
    )
