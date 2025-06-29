from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

console = Console()
app = typer.Typer(name="metroflux", help="CLI for running the weather agent.")


@app.callback()
def load_env(
    env: Path = typer.Option(
        Path(".env"), "--env", "-e", help="Environment config file"
    ),
):
    if not env.exists():
        console.print("[red]Environment config file not found[/red]")
        return
    load_dotenv(dotenv_path=env, override=True)
    console.print("[green]Environment config file loaded[/green]")


if __name__ == "__main__":
    app()