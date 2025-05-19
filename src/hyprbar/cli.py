# Command Line Interface for hyprbar
# Using click for command line interface
import sys
import click
from rich.table import Table
from hyprbar.bar import runHyprBar  # pyright: ignore # noqa
from hyprbar.config import HyprbarConfig  # pyright: ignore # noqa
from hyprbar.util import cl, showError, fileExists
from hyprbar.constants import APP_NAME, APP_VERSION, CONFIG_FILE, STYLE_FILE


@click.command()
def cli() -> None:
    """
    Command line interface for hyprbar.
    """
    cl.print(
        f"[bold green]{APP_NAME}[/bold green] [bold blue]{APP_VERSION}[/bold blue]"
    )

    cl.print("Configuration Status...")
    # Criação da tabela
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Item", justify="right")
    table.add_column("Path")
    table.add_column("Status", justify="center")

    configFileOk = fileExists(file=CONFIG_FILE)
    styleFileOk = fileExists(file=STYLE_FILE)
    table.add_row(
        "Config",
        f"[yellow]{CONFIG_FILE}[/yellow]",
        f"{'[bold green]Passed[/bold green]' if configFileOk else '[bold red]Fail[/bold red]'}",
    )
    table.add_row(
        "Style",
        f"[yellow]{STYLE_FILE}[/yellow]",
        f"{'[bold green]Passed[/bold green]' if styleFileOk else '[bold red]Fail[/bold red]'}",
    )

    cl.print(table)

    if not configFileOk:
        showError(f"{CONFIG_FILE} does not exist. Exiting...")
        sys.exit(1)

    if not styleFileOk:
        showError("Style file does not exists... Exiting...")
        sys.exit(1)

    try:
        hyprbarConfig = HyprbarConfig()  # pyright: ignore # noqa
        cl.print("Starting GUI...")
        runHyprBar(config=hyprbarConfig)
    except Exception as e:
        showError(f"Error: {e}")
