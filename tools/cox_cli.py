# pyright: reportMissingTypeStubs=false

from __future__ import annotations

from pathlib import Path

import typer  # type: ignore[import-untyped]
from rich.console import Console  # type: ignore[import-untyped]
from rich.table import Table  # type: ignore[import-untyped]

from . import __version__
from .cox_lib import CoxError, compile_project, validate_project


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Validate and compile COX projects.",
)
console = Console()


def print_validation_summary(
    project_label: str,
    document_count: int,
    warnings: list[str],
) -> None:
    table = Table(show_header=False, box=None)
    table.add_row("Project", project_label)
    table.add_row("Validated documents", str(document_count))
    table.add_row("Warnings", str(len(warnings)))
    console.print(table)
    for warning in warnings:
        console.print(f"[yellow]- {warning}[/yellow]")


@app.command("validate")
def validate_command(
    project_path: Path = typer.Argument(
        Path("."),
        exists=True,
        resolve_path=True,
    ),
) -> None:
    """Validate all COX documents referenced by manifest.cox."""
    try:
        summary = validate_project(project_path)
    except CoxError as exc:
        console.print(f"[bold red]Validation failed[/bold red]\n{exc}")
        raise typer.Exit(code=1) from exc

    console.print(
        "[bold green]COX validation passed[/bold green] "
        f"[dim](v{__version__})[/dim]"
    )
    print_validation_summary(
        summary.project_root.as_posix(),
        len(summary.documents),
        summary.warnings,
    )


@app.command("compile")
def compile_command(
    project_path: Path = typer.Argument(
        Path("."),
        exists=True,
        resolve_path=True,
    ),
    out_dir: Path = typer.Option(
        Path("build"),
        "--out",
        "-o",
        resolve_path=False,
    ),
) -> None:
    """Validate the project and emit normalized JSON outputs."""
    try:
        result = compile_project(project_path, out_dir)
    except CoxError as exc:
        console.print(f"[bold red]Compilation failed[/bold red]\n{exc}")
        raise typer.Exit(code=1) from exc

    console.print(
        "[bold green]COX compilation passed[/bold green] "
        f"[dim](v{__version__})[/dim]"
    )
    table = Table(show_header=False, box=None)
    table.add_row("Build root", result["build_root"].as_posix())
    table.add_row("Normalized documents", str(result["normalized_count"]))
    table.add_row("Compiled manifest", result["compiled_manifest"].as_posix())
    table.add_row("Verification report", result["report"].as_posix())
    console.print(table)
    for warning in result["warnings"]:
        console.print(f"[yellow]- {warning}[/yellow]")


if __name__ == "__main__":
    app()
