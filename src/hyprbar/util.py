# Utils Functions
#
import os
import subprocess
from rich.console import Console
from hyprbar.constants import SPACES_DEFAULT

cl = Console()


def showStatus(preamble: str, message: str) -> None:
    cl.print(f"[bold yellow]{preamble:<{SPACES_DEFAULT}}[/bold yellow]: {message}")


def showError(message: str) -> None:
    error = "ERROR"
    cl.print(f"[bold red]{error:<{SPACES_DEFAULT}}[/bold red]: {message}")


def configFileExists(configFile: str) -> bool:
    if os.path.isfile(configFile):
        return True
    else:
        return False


def configDirExists(configDir: str) -> bool:
    if os.path.isdir(configDir):
        return True
    else:
        return False


def executeCommand(command: str) -> tuple[int, str, str]:
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr
