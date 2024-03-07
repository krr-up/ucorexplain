"""
UCOREXPLAIN
"""

from typing import Final, Optional, Sequence, Union

import clingo
import typeguard
from dumbo_asp.primitives.atoms import GroundAtom, SymbolicAtom
from dumbo_asp.primitives.models import Model
from dumbo_asp.primitives.predicates import Predicate
from dumbo_asp.primitives.programs import SymbolicProgram
from dumbo_asp.primitives.rules import SymbolicRule
from dumbo_utils.console import console
import base64

import os
from clingo import Control
from clingo.script import enable_python
from clingraph.clingo_utils import ClingraphContext  # type: ignore
from clingraph.graphviz import compute_graphs, render  # type: ignore
from clingraph.orm import Factbase  # type: ignore
from clingraph.clingo_utils import add_svg_interaction, add_elements_ids

AnswerSetElement = Union[GroundAtom, tuple[GroundAtom, bool]]
AnswerSet = tuple[AnswerSetElement, ...]

MUS_PREDICATE: Final = f"__mus__"


def path(file: str) -> str:
    import pathlib

    directory = pathlib.Path(__file__).parent.resolve() / ".."
    return str(directory / file)


def file_to_str(file: str) -> str:
    with open(path(file)) as f:
        return f.read()


def program_from_files(files) -> SymbolicProgram:
    return SymbolicProgram.parse("\n".join(file_to_str(file) for file in files))


def print_with_title(title, value, quiet=False):
    # return
    if quiet:
        return
    console.print(f"[bold red]{title}:[/bold red]")

    if type(value) is list:
        for e in value:
            console.print(f"{e}")
    else:
        console.print(f"{value}")
    console.print(f"[bold red]-------------[/bold red]")


ENCODINGS_PATH = os.path.join(".", os.path.join("ucorexplain", "encodings"))


def visualize(file_path) -> None:
    fb = Factbase(prefix="viz_")
    ctl = Control([])
    ctx = ClingraphContext()
    add_elements_ids(ctl)
    ctl.load(file_path)
    ctl.load(os.path.join(ENCODINGS_PATH, "clingraph.lp"))
    enable_python()

    ctl.ground([("base", [])], context=ctx)
    ctl.solve(on_model=fb.add_model)
    graphs = compute_graphs(fb, graphviz_type="digraph")
    path_png = render(graphs, format="png")
    print("PNG Image saved in: " + path_png["default"])
    paths = render(graphs, view=True, format="svg")
    add_svg_interaction([paths])
    print(
        "SVG Image saved in: "
        + paths["default"]
        + "      Click on the nodes to expand! If your browser is opening empty, you might have to scroll to the side to find the first node"
    )


def ruleto64(rule_str):
    s = str(rule_str).strip('"')
    r = SymbolicRule.parse(s)
    r = r.with_chopped_body(
        with_backward_search=True, backward_search_symbols=(";", " :-")
    )
    encoded = base64.b64encode(str(r).encode("ascii"))
    return encoded


def save_graph(graph):
    with open("graph.lp", "wb") as file_to_save:
        for a in graph:
            file_to_save.write((a.predicate_name).encode())
            file_to_save.write(
                "({}".format(
                    ",".join([str(a).strip('"') for a in a.arguments[:-1]])
                ).encode()
            )

            if a.predicate_name == "node":
                t = a.arguments[-1].arguments
                file_to_save.write(", (".encode())
                file_to_save.write(str(t[0]).encode())
                if len(t) > 1:
                    file_to_save.write(', "'.encode())
                    s = ruleto64(str(t[1]))
                    file_to_save.write(s)
                    file_to_save.write('"'.encode())
                    if len(t) == 3:
                        file_to_save.write(",".encode())
                        file_to_save.write(str(t[2]).encode())
                file_to_save.write(")".encode())
            if a.predicate_name == "link":
                s = ruleto64(str(a.arguments[-1]))
                file_to_save.write(', "'.encode())
                file_to_save.write(s)
                file_to_save.write('"'.encode())

            file_to_save.write(").\n".encode())
