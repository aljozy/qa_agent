"""Test the CLI interface."""

from typer.testing import CliRunner

from qa_agent.cli import app

runner = CliRunner()


def test_cli_version() -> None:
    """Test the --version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "QA Agent version: 0.1.0" in result.stdout


def test_cli_help() -> None:
    """Test the --help flag."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AI-Powered QA Agent" in result.stdout


def test_cli_no_args() -> None:
    """Test CLI with no arguments shows help."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "AI-Powered QA Agent" in result.stdout
