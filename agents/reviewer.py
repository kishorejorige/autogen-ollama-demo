from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient


def create_code_reviewer_agent(
    model_client: OllamaChatCompletionClient,
) -> AssistantAgent:
    return AssistantAgent(
        name="code_reviewer",
        model_client=model_client,
        system_message=(
            "You are a senior Python code reviewer.\n\n"
            "Responsibilities:\n"
            "1. Review Python code for correctness, readability, security, maintainability, and edge cases.\n"
            "2. Provide concise feedback.\n"
            "3. Do not rewrite the full solution unless necessary.\n"
            "4. At the end of your feedback, you MUST output a review status line strictly in one of these two formats:\n"
            "   Review status: APPROVED\n"
            "   or\n"
            "   Review status: CHANGES_REQUIRED"
        ),
    )
