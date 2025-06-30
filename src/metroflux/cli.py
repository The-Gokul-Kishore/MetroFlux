from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from typing import List
import os
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

@app.command()
def run_backend():
    from metroflux.server import api
    api()

@app.command()
def run_frontend(
    frontend_command: List[str] = typer.Option(
        ["npm", "run", "dev"],
        help="Command to run the frontend"
    )
):
    from subprocess import run

    frontend_dir = Path(__file__).resolve().parents[2] / os.getenv("FRONTEND_PATH", "frontend")

    print(f"Running frontend at {frontend_dir} with command: {' '.join(frontend_command)}")
    run(frontend_command, cwd=frontend_dir,shell=True)


if __name__ == "__main__":
    app()