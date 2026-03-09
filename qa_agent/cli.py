"""Command-line interface for the QA Agent."""

import typer
from typing import Optional

app = typer.Typer(
    name="qa-agent",
    help="AI-Powered QA Agent for intelligent test automation and artifact generation",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit"),
) -> None:
    """AI-Powered QA Agent for intelligent test automation and artifact generation."""
    if version:
        from qa_agent import __version__

        typer.echo(f"QA Agent version: {__version__}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app()
