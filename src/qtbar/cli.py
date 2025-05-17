# Command Line Interface for qtbar
# Using click for command line interface
import sys
import click

# from qtbar.config import qtbarConfig
from qtbar.util import cl, configDirExists, showStatus, showError, configFileExists
from qtbar.constants import APP_NAME, APP_VERSION, CONFIG_DIR, CONFIG_FILE


@click.command()
def cli() -> None:
    """
    Command line interface for qtbar.
    """

    try:
        cl.print(
            f"[bold green]{APP_NAME}[/bold green] [bold blue]{APP_VERSION}[/bold blue]"
        )

        # Check Config directory
        exists = configDirExists(configDir=CONFIG_DIR)
        cl.print(f"Diectory exists? ===> {exists}")
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
                # qtbarConfig = qtbarConfig()
                # showStatus("qtbarConfig", f"{qtbarConfig}")
            else:
                showStatus(
                    "Config File",
                    f"{CONFIG_FILE} [bold red][{exists}][/bold red]",
                )
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
