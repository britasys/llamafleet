import subprocess

import typer

from app.core.config import get_config

cli = typer.Typer()


@cli.command()
def serve():
    config = get_config()
    subprocess.run(
        [
            "uvicorn",
            "app.main:app",
            "--host",
            config.server.host,
            "--port",
            str(config.server.port),
        ],
        check=True,
    )


@cli.command()
def config():
    print(get_config().model_dump_json(indent=2))


def main():
    cli()
