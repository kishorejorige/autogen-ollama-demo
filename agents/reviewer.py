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
            "4. You MUST output your review decision as a structured JSON block inside a markdown code block:\n"
            "   ```json\n"
            "   {\n"
            "     \"status\": \"APPROVED\" or \"CHANGES_REQUIRED\",\n"
            "     \"feedback\": \"Your concise reviewer feedback here\"\n"
            "   }\n"
            "   ```\n"
            "5. At the very end of your response, also output a status line in one of these formats:\n"
            "   Review status: APPROVED\n"
            "   or\n"
            "   Review status: CHANGES_REQUIRED"
        ),
    )
