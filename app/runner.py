from autogen_agentchat.ui import Console
from autogen_ext.models.ollama import OllamaChatCompletionClient

from agents.assistant import create_python_assistant
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL


async def run() -> None:
    model_client = OllamaChatCompletionClient(
        model=OLLAMA_MODEL,
        host=OLLAMA_BASE_URL,
    )

    try:
        agent = create_python_assistant(model_client)

        await Console(
            agent.run_stream(
                task="Explain what an AI agent is in two simple sentences."
            )
        )
    finally:
        await model_client.close()
