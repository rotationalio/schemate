"""
Primary entry point for schemate CLI application
"""

import os
import sys
import colorama
import argparse

from .config import Config
from .version import get_version
from .exceptions import SchemateException, CommandError


def analyze(args: argparse.Namespace) -> None:
    """
    CLI entry point for analyzing documents.
    """
    config = Config.load(args.config)
    print(config)


##########################################################################
## CLI Helpers
##########################################################################

class SchemateFormatter(argparse.ArgumentDefaultsHelpFormatter):

    def __init__(self, *args, **kwargs):
        if "width" not in kwargs:
            try:
                kwargs["width"] = os.get_terminal_size().columns
            except OSError:
                pass

        if "max_help_position" not in kwargs:
            kwargs["max_help_position"] = 32

        super().__init__(*args, **kwargs)


class Environ(argparse.Action):

    def __init__(self, envvar, required=True, default=None, **kwargs):
        if envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False
        super(Environ, self).__init__(default=default, required=required, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


##########################################################################
## CLI Main Entry Point
##########################################################################

# argparse application description
DESCRIPTION = "Analyzes groups of documents and generates a schema profile for them."
EPILOG = "Created with ♠ by the Rotational Labs team."

# argparse commands
CMDS = {
    "analyze": {
        "help": "analyze documents and generate a schema profile",
        "func": analyze,
        "args": {
            ("-c", "--config"): {
                "metavar": "PATH", "default": None, "type": str, ""
                "action": Environ, "envvar": "SCHEMATE_CONFIG",
                "help": "path to the configuration file for the analysis (env: $SCHEMATE_CONFIG)",
            },
            ("-o", "--output"): {
                "metavar": "PATH", "default": None, "type": str,
                "help": "write the schema profile to a file instead of stdout",
            },
        },
    },
}


def main():
    """
    Main entry point for schemate CLI application.
    """
    colorama.init(autoreset=True)
    parser = argparse.ArgumentParser(
        prog="schemate",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=SchemateFormatter,
    )

    # Add version information
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
        help="Show the version and exit.",
    )

    # Create subparsers for each command
    subparsers = parser.add_subparsers(title="actions")
    for cmd, cargs in CMDS.items():
        ckws = {"help": cargs.get("help"), "formatter_class": SchemateFormatter}
        subparser = subparsers.add_parser(cmd, **ckws)
        subparser.set_defaults(func=cargs.get("func"))

        for pargs, kwargs in cargs.get("args", {}).items():
            if isinstance(pargs, str):
                pargs = (pargs,)
            subparser.add_argument(*pargs, **kwargs)

    # Execute the argparse CLI parser and associated command
    args = parser.parse_args()
    if hasattr(args, "func"):
        try:
            args.func(args)
        except CommandError as e:
            parser.error(e)
        except SchemateException as e:
            print(colorama.Fore.RED + str(e))
            sys.exit(2)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
