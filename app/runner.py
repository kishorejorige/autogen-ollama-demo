from autogen_agentchat.ui import Console
from autogen_ext.models.ollama import OllamaChatCompletionClient

from agents.developer import create_python_developer_agent
from agents.manager import create_manager_agent
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL


async def run() -> None:
    model_client = OllamaChatCompletionClient(
        model=OLLAMA_MODEL,
        host=OLLAMA_BASE_URL,
    )

    try:
        manager_agent = create_manager_agent(model_client)
        developer_agent = create_python_developer_agent(model_client)

        task = (
            "Create a simple Python function that returns whether a number "
            "is even or odd."
        )

        await Console(
            manager_agent.run_stream(
                task=(
                    f"Review this task and identify the correct specialist: {task}"
                )
            )
        )

        await Console(
            developer_agent.run_stream(
                task=task,
            )
        )
    finally:
        await model_client.close()
