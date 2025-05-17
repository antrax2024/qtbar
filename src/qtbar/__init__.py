# - This is a Python 3.13 application
# - Enforce static typing (type hints) in all functions
# - Enable rich terminal output using `rich`
# - Manage Python dependencies and builds with `uv`
# - Adhere to PEP8 code style standards
# - Maintain English-only documentation and code comments
# - Apply camelCase convention for variables, methods and functions
# **Note**: While camelCase conflicts with PEP8's snake_case recommendation
# for Python, this requirement takes precedence per project specifications
def main() -> None:
    from qtbar.cli import cli

    # call Command Line Interface
    cli()
