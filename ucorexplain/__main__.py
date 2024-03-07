"""
The main entry point for the application.
"""

import sys

from dumbo_asp.primitives.models import Model
from dumbo_asp.queries import explanation_graph, pack_xasp_navigator_url

from ucorexplain import print_with_title, program_from_files, visualize, save_graph
from .utils.parser import get_parser

old_stdout = sys.stdout


def main():
    """
    Run the main function.
    """
    parser = get_parser()
    args = parser.parse_args()
    quiet = not args.verbose
    # Program
    program = program_from_files([f.name for f in args.prg])
    print_with_title("INPUT PROGRAM", program, quiet)

    answer_set = Model.of_program(args.answer)
    print_with_title("Answer set", answer_set, quiet)

    # # Query TODO extend for multiple atoms in query
    query = Model.of_atoms(args.query)
    print_with_title("Query", query, quiet)

    explicitly_mentioned_atoms = Model.of_program(args.false)
    print_with_title("Explicit false", explicitly_mentioned_atoms, quiet)

    zero_simplification_prg = program.to_zero_simplification_version(
        extra_atoms=(*answer_set, *query, *explicitly_mentioned_atoms),
        compact=True,
    )
    print_with_title("Zero_simplification_version", zero_simplification_prg, quiet)

    herbrand_base = zero_simplification_prg.herbrand_base_without_false_predicate
    print_with_title("Herbrand base without zero", herbrand_base, quiet)

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
