# Command Line Interface for hyprbar
# Using click for command line interface
import sys
import click

from hyprbar.config import HyprbarConfig
from hyprbar.util import cl, configDirExists, showStatus, showError, configFileExists
from hyprbar.constants import APP_NAME, APP_VERSION, CONFIG_DIR, CONFIG_FILE
from hyprbar.bar import runHyprBar


@click.command()
def cli() -> None:
    """
    Command line interface for hyprbar.
    """

    try:
        cl.print(
            f"[bold green]{APP_NAME}[/bold green] [bold blue]{APP_VERSION}[/bold blue]"
        )

        # Check Config directory
        exists = configDirExists(configDir=CONFIG_DIR)
        if exists:
            showStatus(
                "Config Dir",
                f"{CONFIG_DIR} [bold green][{exists}][/bold green]",
            )
            # Now test if config file exists
            exists = configFileExists(configFile=CONFIG_FILE)
            if exists:
                showStatus(
                    "Config File",
                    f"{CONFIG_FILE} [bold green][{exists}][/bold green]",
                )
                try:
                    hyprbarConfig = HyprbarConfig()  # pyright: ignore # noqa
                    showStatus(
                        "Config Valid",
                        "Configuration loaded and validated [bold green][Success][/bold green]",
                    )
                    runHyprBar()
                except Exception as e:
                    showError(f"Invalid config file => {e}")
            else:
                showError("Config file does not exist. Exiting...")
                sys.exit(1)
        else:
            showStatus(
                "Config Dir",
                f"{CONFIG_DIR} [bold red][{exists}][/bold red]",
            )
            showError("Config directory does not exist. Exiting...")
            sys.exit(1)

    except Exception as e:
        showError(f"{e}")
