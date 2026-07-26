import asyncio
import sys

from app.runner import run


def get_task() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]).strip()

    return input("Enter your task: ").strip()


def main() -> None:
    task = get_task()

    if not task:
        print("Error: A task is required.")
        raise SystemExit(1)

    asyncio.run(run(task))


if __name__ == "__main__":
    main()
