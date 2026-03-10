"""Command-line interface for the QA Agent."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from qa_agent import __version__
from qa_agent.analysis.rtm_generator import RTMGenerator
from qa_agent.config import Config
from qa_agent.core.exceptions import ConfigurationError, LLMError, ParsingError, StorageError
from qa_agent.core.logging_config import setup_logging
from qa_agent.generators.manual_test_generator import ManualTestGenerator
from qa_agent.llm.client import LLMClient
from qa_agent.parsers.markdown_parser import MarkdownParser
from qa_agent.storage.file_storage import FileStorage

app = typer.Typer(
    name="qa-agent",
    help="AI-Powered QA Agent for intelligent test automation and artifact generation",
    add_completion=False,
)

console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit"),
) -> None:
    """AI-Powered QA Agent for intelligent test automation and artifact generation."""
    if version:
        console.print(f"[bold blue]QA Agent[/bold blue] version: {__version__}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


@app.command()
def parse(
    input_file: Path = typer.Argument(
        ...,
        help="Path to the markdown requirements file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output_dir: Path = typer.Option(
        "output/requirements",
        "--output",
        "-o",
        help="Output directory for parsed requirements",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (optional)",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    ),
    json_logs: bool = typer.Option(
        False,
        "--json-logs",
        help="Output logs in JSON format for CI/CD",
    ),
) -> None:
    """
    Parse markdown requirements and save to JSON.
    
    This command parses a markdown document containing requirements and saves
    the structured requirements to a JSON file for later use.
    """
    # Initialize logging
    setup_logging(
        log_level=log_level,
        log_to_file=True,
        log_to_console=True,
        json_format=json_logs,
    )
    
    try:
        # Load configuration if provided
        if config_file:
            config = Config.from_yaml(config_file)
        else:
            config = Config()
        
        # Override output directory
        config.output.directory = output_dir
        config.ensure_output_directory()
        
        console.print(f"[bold]Parsing requirements from:[/bold] {input_file}")
        
        # Parse requirements
        parser = MarkdownParser()
        
        with console.status("[bold green]Parsing markdown document..."):
            requirements = parser.parse_file(input_file)
        
        if not requirements:
            console.print("[yellow]Warning:[/yellow] No requirements found in the document")
            raise typer.Exit(1)
        
        console.print(f"[green]✓[/green] Parsed {len(requirements)} requirements")
        
        # Save requirements
        storage = FileStorage(output_dir)
        filename = input_file.stem  # Use input filename without extension
        
        with console.status("[bold green]Saving requirements..."):
            output_path = storage.save(requirements, filename)
        
        console.print(f"[green]✓[/green] Saved requirements to: {output_path}")
        console.print(f"\n[bold green]Success![/bold green] Parsed {len(requirements)} requirements")
        
    except ParsingError as e:
        console.print(f"[bold red]Parsing Error:[/bold red] {e.message}", style="red")
        if e.details:
            console.print(f"[dim]Details: {e.details}[/dim]")
        raise typer.Exit(1)
    except StorageError as e:
        console.print(f"[bold red]Storage Error:[/bold red] {e.message}", style="red")
        if e.details:
            console.print(f"[dim]Details: {e.details}[/dim]")
        raise typer.Exit(1)
    except ConfigurationError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e.message}", style="red")
        if e.details:
            console.print(f"[dim]Details: {e.details}[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
        raise typer.Exit(1)


@app.command()
def generate(
    requirements_file: Path = typer.Argument(
        ...,
        help="Path to the requirements JSON file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output_dir: Path = typer.Option(
        "output/tests",
        "--output",
        "-o",
        help="Output directory for generated test cases",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (optional)",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="Override AI provider (kiro/openai)",
    ),
    positive: bool = typer.Option(
        True,
        "--positive/--no-positive",
        help="Generate positive test scenarios",
    ),
    negative: bool = typer.Option(
        True,
        "--negative/--no-negative",
        help="Generate negative test scenarios",
    ),
    edge_cases: bool = typer.Option(
        True,
        "--edge-cases/--no-edge-cases",
        help="Generate edge case test scenarios",
    ),
) -> None:
    """
    Generate test cases from requirements.
    
    This command loads requirements from a JSON file and generates manual test
    cases using AI. The test cases are saved to JSON format.
    """
    try:
        # Load configuration
        if config_file:
            config = Config.from_yaml(config_file)
        else:
            # Try to load default config
            default_config = Path("config.kiro.yaml")
            if default_config.exists():
                config = Config.from_yaml(default_config)
            else:
                config = Config()
        
        # Override provider if specified
        if provider:
            if provider not in ["kiro", "openai"]:
                console.print(f"[bold red]Error:[/bold red] Invalid provider '{provider}'. Must be 'kiro' or 'openai'")
                raise typer.Exit(1)
            config.ai.provider = provider
        
        # Override output directory
        config.output.directory = output_dir
        config.ensure_output_directory()
        
        console.print(f"[bold]Generating test cases from:[/bold] {requirements_file}")
        console.print(f"[bold]AI Provider:[/bold] {config.ai.provider}")
        console.print(f"[bold]Model:[/bold] {config.ai.model}")
        
        # Load requirements
        storage = FileStorage(requirements_file.parent)
        
        with console.status("[bold green]Loading requirements..."):
            requirements = storage.load(requirements_file.name)
        
        if not requirements:
            console.print("[yellow]Warning:[/yellow] No requirements found in file")
            raise typer.Exit(1)
        
        console.print(f"[green]✓[/green] Loaded {len(requirements)} requirements")
        
        # Initialize LLM client and generator
        llm_client = LLMClient(config.ai)
        generator = ManualTestGenerator(llm_client)
        
        # Generate test cases with progress tracking
        console.print(f"\n[bold]Generating test cases...[/bold]")
        console.print(f"  Positive scenarios: {positive}")
        console.print(f"  Negative scenarios: {negative}")
        console.print(f"  Edge cases: {edge_cases}")
        
        test_artifacts = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Processing 0/{len(requirements)} requirements...",
                total=len(requirements)
            )
            
            def progress_callback(completed: int, total: int, req_id: str) -> None:
                progress.update(
                    task,
                    completed=completed,
                    description=f"Processing {completed}/{total} requirements... (last: {req_id})"
                )
            
            # Run async generation
            test_artifacts = asyncio.run(
                generator.generate(
                    requirements=requirements,
                    include_positive=positive,
                    include_negative=negative,
                    include_edge_cases=edge_cases,
                    progress_callback=progress_callback,
                )
            )
        
        if not test_artifacts:
            console.print("[yellow]Warning:[/yellow] No test cases generated")
            raise typer.Exit(1)
        
        console.print(f"[green]✓[/green] Generated {len(test_artifacts)} test cases")
        
        # Save test artifacts
        output_file = output_dir / f"{requirements_file.stem}_tests.json"
        
        with console.status("[bold green]Saving test cases..."):
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                artifacts_data = [artifact.model_dump(mode="json") for artifact in test_artifacts]
                json.dump(artifacts_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✓[/green] Saved test cases to: {output_file}")
        console.print(f"\n[bold green]Success![/bold green] Generated {len(test_artifacts)} test cases")
        
    except LLMError as e:
        console.print(f"[bold red]LLM Error:[/bold red] {str(e)}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
        raise typer.Exit(1)


@app.command()
def rtm(
    requirements_file: Path = typer.Argument(
        ...,
        help="Path to the requirements JSON file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    tests_file: Path = typer.Argument(
        ...,
        help="Path to the test artifacts JSON file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output_dir: Path = typer.Option(
        "output/rtm",
        "--output",
        "-o",
        help="Output directory for RTM",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (optional)",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
) -> None:
    """
    Generate Requirement Traceability Matrix (RTM).
    
    This command creates an RTM mapping requirements to test cases and
    calculates coverage metrics. The RTM is exported to CSV format.
    """
    try:
        # Load configuration if provided
        if config_file:
            config = Config.from_yaml(config_file)
        else:
            config = Config()
        
        # Override output directory
        config.output.directory = output_dir
        config.ensure_output_directory()
        
        console.print(f"[bold]Generating RTM from:[/bold]")
        console.print(f"  Requirements: {requirements_file}")
        console.print(f"  Tests: {tests_file}")
        
        # Load requirements
        req_storage = FileStorage(requirements_file.parent)
        
        with console.status("[bold green]Loading requirements..."):
            requirements = req_storage.load(requirements_file.name)
        
        console.print(f"[green]✓[/green] Loaded {len(requirements)} requirements")
        
        # Load test artifacts
        with console.status("[bold green]Loading test artifacts..."):
            with open(tests_file, "r", encoding="utf-8") as f:
                from qa_agent.models.base import TestArtifact
                artifacts_data = json.load(f)
                test_artifacts = [TestArtifact(**data) for data in artifacts_data]
        
        console.print(f"[green]✓[/green] Loaded {len(test_artifacts)} test artifacts")
        
        # Generate RTM
        rtm_generator = RTMGenerator()
        
        with console.status("[bold green]Generating RTM..."):
            rtm_entries = rtm_generator.generate(requirements, test_artifacts)
            coverage_pct = rtm_generator.calculate_coverage_percentage(requirements, test_artifacts)
            uncovered = rtm_generator.identify_uncovered_requirements(requirements, test_artifacts)
        
        console.print(f"[green]✓[/green] Generated RTM with {len(rtm_entries)} entries")
        console.print(f"[bold]Coverage:[/bold] {coverage_pct:.1f}%")
        
        if uncovered:
            console.print(f"[yellow]Warning:[/yellow] {len(uncovered)} requirements have no test coverage")
        
        # Export RTM to CSV
        output_file = output_dir / "rtm.csv"
        
        with console.status("[bold green]Exporting RTM to CSV..."):
            rtm_generator.export_to_csv(rtm_entries, output_file)
        
        console.print(f"[green]✓[/green] Exported RTM to: {output_file}")
        console.print(f"\n[bold green]Success![/bold green] Generated RTM with {coverage_pct:.1f}% coverage")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
        raise typer.Exit(1)


@app.command()
def run(
    input_file: Path = typer.Argument(
        ...,
        help="Path to the markdown requirements file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output_dir: Path = typer.Option(
        "output",
        "--output",
        "-o",
        help="Base output directory for all artifacts",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (optional)",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="Override AI provider (kiro/openai)",
    ),
) -> None:
    """
    Run the full pipeline: parse → generate → rtm.
    
    This command executes the complete workflow from parsing requirements
    to generating test cases and creating an RTM.
    """
    try:
        console.print("[bold blue]QA Agent - Full Pipeline[/bold blue]\n")
        
        # Load configuration
        if config_file:
            config = Config.from_yaml(config_file)
        else:
            # Try to load default config
            default_config = Path("config.kiro.yaml")
            if default_config.exists():
                config = Config.from_yaml(default_config)
            else:
                config = Config()
        
        # Override provider if specified
        if provider:
            if provider not in ["kiro", "openai"]:
                console.print(f"[bold red]Error:[/bold red] Invalid provider '{provider}'. Must be 'kiro' or 'openai'")
                raise typer.Exit(1)
            config.ai.provider = provider
        
        # Set up output directories
        req_dir = output_dir / "requirements"
        tests_dir = output_dir / "tests"
        rtm_dir = output_dir / "rtm"
        
        # Step 1: Parse requirements
        console.print("[bold]Step 1/3: Parsing requirements[/bold]")
        parser = MarkdownParser()
        
        with console.status("[bold green]Parsing markdown document..."):
            requirements = parser.parse_file(input_file)
        
        if not requirements:
            console.print("[yellow]Warning:[/yellow] No requirements found")
            raise typer.Exit(1)
        
        console.print(f"[green]✓[/green] Parsed {len(requirements)} requirements")
        
        # Save requirements
        req_storage = FileStorage(req_dir)
        filename = input_file.stem
        req_file = req_storage.save(requirements, filename)
        console.print(f"[green]✓[/green] Saved to: {req_file}\n")
        
        # Step 2: Generate test cases
        console.print("[bold]Step 2/3: Generating test cases[/bold]")
        console.print(f"[bold]AI Provider:[/bold] {config.ai.provider}")
        console.print(f"[bold]Model:[/bold] {config.ai.model}")
        
        llm_client = LLMClient(config.ai)
        generator = ManualTestGenerator(llm_client)
        
        test_artifacts = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Processing 0/{len(requirements)} requirements...",
                total=len(requirements)
            )
            
            def progress_callback(completed: int, total: int, req_id: str) -> None:
                progress.update(
                    task,
                    completed=completed,
                    description=f"Processing {completed}/{total} requirements..."
                )
            
            test_artifacts = asyncio.run(
                generator.generate(
                    requirements=requirements,
                    include_positive=True,
                    include_negative=True,
                    include_edge_cases=True,
                    progress_callback=progress_callback,
                )
            )
        
        if not test_artifacts:
            console.print("[yellow]Warning:[/yellow] No test cases generated")
            raise typer.Exit(1)
        
        console.print(f"[green]✓[/green] Generated {len(test_artifacts)} test cases")
        
        # Save test artifacts
        tests_dir.mkdir(parents=True, exist_ok=True)
        tests_file = tests_dir / f"{filename}_tests.json"
        
        with open(tests_file, "w", encoding="utf-8") as f:
            artifacts_data = [artifact.model_dump(mode="json") for artifact in test_artifacts]
            json.dump(artifacts_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✓[/green] Saved to: {tests_file}\n")
        
        # Step 3: Generate RTM
        console.print("[bold]Step 3/3: Generating RTM[/bold]")
        
        rtm_generator = RTMGenerator()
        
        with console.status("[bold green]Generating RTM..."):
            rtm_entries = rtm_generator.generate(requirements, test_artifacts)
            coverage_pct = rtm_generator.calculate_coverage_percentage(requirements, test_artifacts)
        
        console.print(f"[green]✓[/green] Generated RTM with {len(rtm_entries)} entries")
        console.print(f"[bold]Coverage:[/bold] {coverage_pct:.1f}%")
        
        # Export RTM
        rtm_dir.mkdir(parents=True, exist_ok=True)
        rtm_file = rtm_dir / "rtm.csv"
        rtm_generator.export_to_csv(rtm_entries, rtm_file)
        
        console.print(f"[green]✓[/green] Saved to: {rtm_file}\n")
        
        # Summary
        console.print("[bold green]Pipeline Complete![/bold green]")
        console.print(f"  Requirements: {len(requirements)}")
        console.print(f"  Test Cases: {len(test_artifacts)}")
        console.print(f"  Coverage: {coverage_pct:.1f}%")
        console.print(f"\n[bold]Output Directory:[/bold] {output_dir}")
        
    except LLMError as e:
        console.print(f"\n[bold red]LLM Error:[/bold red] {str(e)}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}", style="red")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
