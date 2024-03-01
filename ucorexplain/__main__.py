"""
The main entry point for the application.
"""

from dumbo_asp.queries import open_graph_in_xasp_navigator, explanation_graph
from dumbo_asp.primitives.models import Model
from dumbo_asp.primitives.atoms import SymbolicAtom, GroundAtom
from dumbo_asp.primitives.programs import SymbolicProgram

from ucorexplain import print_with_title, program_from_files, visualize, save_graph

# from .meta import run_meta
from .utils.parser import get_parser

# from dumbo_asp.queries import open_graph_in_xasp_navigator
import sys
from io import StringIO  # Python3 use: from io import StringIO
import sys

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

    if args.navegate:
        # show DAG
        open_graph_in_xasp_navigator(
            graph,
            with_chopped_body=True,
            with_backward_search=True,
            backward_search_symbols=(";", " :-"),
        )

    if quiet and not args.view and not args.navegate:
        print("Use --view or --navegate to see the graph")


if __name__ == "__main__":
    main()
