# Command Line Interface for hyprbar
# Using click for command line interface
import sys
import click

from hyprbar.config import HyprbarConfig  # pyright: ignore # noqa
from hyprbar.util import cl, showStatus, showError, fileExists, printLine
from hyprbar.constants import APP_NAME, APP_VERSION, CONFIG_FILE, STYLE_FILE
from hyprbar.bar import runHyprBar  # pyright: ignore # noqa


@click.command()
def cli() -> None:
    """
    Command line interface for hyprbar.
    """
    cl.print(
        f"[bold green]{APP_NAME}[/bold green] [bold blue]{APP_VERSION}[/bold blue]"
    )
    printLine()
    configFileOk = fileExists(file=CONFIG_FILE)
    if configFileOk:
        showStatus(
            "Config",
            f"{CONFIG_FILE} [bold green][{configFileOk}][/bold green]",
        )
    else:
        showError(f"{CONFIG_FILE} does not exist. Exiting...")
        sys.exit(1)

    styleFileOk = fileExists(file=STYLE_FILE)
    if styleFileOk:
        showStatus(
            preamble="Style",
            message=f"{STYLE_FILE} [bold green][{styleFileOk}][/bold green]",
        )
    else:
        showError("Style file does not exists... Exiting...")
        sys.exit(1)

    printLine()
    try:
        hyprbarConfig = HyprbarConfig()  # pyright: ignore # noqa
        cl.log("Starting HyprBar...")
        runHyprBar(config=hyprbarConfig)
    except Exception as e:
        showError(f"Error: {e}")
