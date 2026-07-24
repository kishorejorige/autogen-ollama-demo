import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.ollama import OllamaChatCompletionClient


async def main() -> None:
    model_client = OllamaChatCompletionClient(
        model="qwen3:1.7b",
        host="http://host.docker.internal:11434",
    )

    agent = AssistantAgent(
        name="python_assistant",
        model_client=model_client,
        system_message=(
            "You are a helpful Python development assistant. "
            "Give clear, concise, and practical answers."
        ),
    )

    await Console(
        agent.run_stream(
            task="Explain what an AI agent is in two simple sentences."
        )
    )

    await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
