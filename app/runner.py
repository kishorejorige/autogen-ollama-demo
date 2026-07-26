from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.ollama import OllamaChatCompletionClient

from agents.developer import create_python_developer_agent
from agents.manager import create_manager_agent
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL


async def run(task: str) -> None:
    model_client = OllamaChatCompletionClient(
        model=OLLAMA_MODEL,
        host=OLLAMA_BASE_URL,
    )

    try:
        manager_agent = create_manager_agent(model_client)
        developer_agent = create_python_developer_agent(model_client)

        termination = MaxMessageTermination(max_messages=3)

        team = RoundRobinGroupChat(
            participants=[
                manager_agent,
                developer_agent,
            ],
            termination_condition=termination,
        )

        await Console(team.run_stream(task=task))
    finally:
        await model_client.close()
