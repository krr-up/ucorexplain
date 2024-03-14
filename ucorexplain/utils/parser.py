"""
The command line parser for the project.
"""

import logging
from argparse import ArgumentParser, FileType, RawTextHelpFormatter
from textwrap import dedent
from typing import Any, cast

from pkg_resources import DistributionNotFound, require

__all__ = ["get_parser"]

try:
    VERSION = require("ucorexplain")[0].version
except DistributionNotFound:  # nocoverage
    VERSION = "local"  # nocoverage


def get_parser() -> ArgumentParser:
    """
    Return the parser for command line options.
    """
    parser = ArgumentParser(
        prog="ucorexplain",
        description=dedent(
            """\
                                      _       _       
  _   _  ___ ___  _ __ _____  ___ __ | | __ _(_)_ __  
 | | | |/ __/ _ \| '__/ _ \ \/ / '_ \| |/ _` | | '_ \ 
 | |_| | (_| (_) | | |  __/>  <| |_) | | (_| | | | | |
  \__,_|\___\___/|_|  \___/_/\_\ .__/|_|\__,_|_|_| |_|
                               |_|   
    
    Explanations for ASP programs via 1-PUS
            """
        ),
        formatter_class=RawTextHelpFormatter,
    )

    levels = [
        ("error", logging.ERROR),
        ("warning", logging.WARNING),
        ("info", logging.INFO),
        ("debug", logging.DEBUG),
    ]

    def get(levels, name):
        for key, val in levels:
            if key == name:
                return val
        return None  # nocoverage

    parser.add_argument(
        "--log",
        default="warning",
        choices=[val for _, val in levels],
        metavar=f"{{{','.join(key for key, _ in levels)}}}",
        help="set log level [%(default)s]",
        type=cast(Any, lambda name: get(levels, name)),
    )

    parser.add_argument(
        "--version", "-v", action="version", version=f"%(prog)s {VERSION}"
    )

    parser.add_argument(
        "--prg", "-p", action="append", help="Program files", type=FileType("r")
    )

    parser.add_argument("--answer", "-a", help="Answer set as facts", default="")
    parser.add_argument(
        "--false", "-f", help="Atoms that are false as facts", default=""
    )

    parser.add_argument("--query", "-q", help="Query atom as facts", required=True)
    parser.add_argument(
        "--view", "-w", help="View with clingraph", default=False, action="store_true"
    )

    parser.add_argument(
        "--move-before",
        "-m",
        help="Moves the given atom (with possible) variables before in the herbrand base giving it preference.",
        action="append",
    )
    parser.add_argument(
        "--view-tree",
        help="View with clingraph as a tree with repeated nodes",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--navigate",
        "-n",
        help="navigate the explanation with navigator",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--verbose",
        help="Verbose mode to show intermediate steps",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--text", "-t", help="View as text", default=False, action="store_true"
    )

    return parser
