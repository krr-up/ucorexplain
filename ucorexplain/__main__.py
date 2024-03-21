"""
The main entry point for the application.
"""

import sys

from dumbo_asp.primitives.programs import SymbolicProgram
from dumbo_asp.primitives.models import Model
from dumbo_asp.queries import explanation_graph, pack_xasp_navigator_url
from dumbo_asp.primitives.atoms import SymbolicAtom, GroundAtom

from ucorexplain import (
    print_with_title,
    program_from_files,
    visualize,
    save_graph,
    print_error,
)
from .utils.parser import get_parser

old_stdout = sys.stdout


def main():
    """
    Run the main function.
    """
    parser = get_parser()
    args = parser.parse_args()
    args.move_before = [] if not args.move_before else args.move_before
    quiet = not args.verbose
    # Program
    program = program_from_files([f.name for f in args.prg])
    print_with_title("INPUT PROGRAM", program, quiet)

    try:
        answer_set = Model.of_program(args.answer)
        print_with_title("Answer set", answer_set, quiet)
    except Exception as e:
        print_error("The answer set should be presented a facts with '.'")
        raise e

    try:
        query = Model.of_program(args.query)
        print_with_title("Query", query, quiet)
    except Exception as e:
        print_error("The query set should be presented a facts with '.'")
        raise e

    try:
        explicitly_mentioned_atoms = Model.of_program(args.false)
        print_with_title("Explicit false", explicitly_mentioned_atoms, quiet)
    except Exception as e:
        print_error("The false atoms set should be presented a facts with '.'")
        raise e

    herbrand_base = SymbolicProgram.of(
        *program,
        *SymbolicProgram.parse(answer_set.as_facts),
        *SymbolicProgram.parse(query.as_facts),
        *SymbolicProgram.parse(explicitly_mentioned_atoms.as_facts),
    ).herbrand_base

    # Move atoms
    herbrand_base = SymbolicProgram.parse(herbrand_base.as_facts)

    for s in args.move_before:
        herbrand_base = herbrand_base.move_before(SymbolicAtom.parse(s))

    print_with_title("Herbrand base", herbrand_base, quiet)

    herbrand_base = tuple(
        GroundAtom.parse(str(rule.head_atom)) for rule in herbrand_base
    )

    # Moving stuff would go here

    # compute DAG
    pus_program = []
    graph = explanation_graph(
        program=program,
        answer_set=answer_set,
        herbrand_base=herbrand_base,
        query=query,
        collect_pus_program=pus_program,
    )
    print_with_title("Grounded Program with selectors", pus_program, quiet)

    print_with_title("Graph", graph, quiet)

    if args.view:
        save_graph(graph)
        visualize("./graph.lp")

    if args.view_tree:
        save_graph(graph)
        visualize("./graph.lp", tree=True)

    if args.navigate:
        # show DAG
        pack_xasp_navigator_url(
            graph,
            open_in_browser=True,
            with_chopped_body=True,
            with_backward_search=True,
            backward_search_symbols=(";", " :-"),
        )

    if quiet and not args.view and not args.navigate:
        print("Use --view or --navigate to see the graph")


if __name__ == "__main__":
    main()
