# app/server/core/logger.py

from rich.console import Console

console = Console()


class AppLogger:
    """
    Colored application logger.

    Provides consistent logging across:

    - Workflow
    - LLM
    - Database
    - LiveKit
    - Evaluation
    """

    @staticmethod
    def info(message: str):
        console.print(
            f"[bold blue][INFO][/bold blue] {message}"
        )

    @staticmethod
    def success(message: str):
        console.print(
            f"[bold green][SUCCESS][/bold green] {message}"
        )

    @staticmethod
    def warning(message: str):
        console.print(
            f"[bold yellow][WARNING][/bold yellow] {message}"
        )

    @staticmethod
    def error(message: str):
        console.print(
            f"[bold red][ERROR][/bold red] {message}"
        )

    @staticmethod
    def debug(message: str):
        console.print(
            f"[dim][DEBUG][/dim] {message}"
        )

    @staticmethod
    def llm(message: str):
        console.print(
            f"[bold magenta][LLM][/bold magenta] {message}"
        )

    @staticmethod
    def workflow(message: str):
        console.print(
            f"[bold cyan][WORKFLOW][/bold cyan] {message}"
        )

    @staticmethod
    def database(message: str):
        console.print(
            f"[bold bright_blue][DATABASE][/bold bright_blue] {message}"
        )

    @staticmethod
    def livekit(message: str):
        console.print(
            f"[bold bright_magenta][LIVEKIT][/bold bright_magenta] {message}"
        )


logger = AppLogger()