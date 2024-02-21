"""
The main entry point for the application.
"""

from dumbo_asp.queries import open_graph_in_xasp_navigator, explanation_graph
from dumbo_asp.primitives.models import Model
from dumbo_asp.primitives.atoms import SymbolicAtom, GroundAtom
from dumbo_asp.primitives.programs import SymbolicProgram

from ucorexplain import (
    print_with_title,
    program_from_files,
)

# from .meta import run_meta
from .utils.parser import get_parser

# from dumbo_asp.queries import open_graph_in_xasp_navigator


def main():
    """
    Run the main function.
    """
    parser = get_parser()
    args = parser.parse_args()

    # Program
    program = program_from_files([f.name for f in args.prg])
    print_with_title("INPUT PROGRAM", program)

    print(args.answer)
    answer_set = Model.of_program(args.answer)
    print_with_title("Answer set", answer_set)

    # # Query TODO extend for multiple atoms in query
    query = Model.of_atoms(args.query)
    print_with_title("Query", query)

    explicitly_mentioned_atoms = Model.of_program(args.false)
    print_with_title("Explicit false", explicitly_mentioned_atoms)

    herbrand_base = program.to_zero_simplification_version(
        extra_atoms=(*answer_set, *query, *explicitly_mentioned_atoms),
        compact=True,
    ).herbrand_base_without_false_predicate
    print_with_title("Herbrand base", herbrand_base)

    # Moving stuff would go here

    # compute DAG
    graph = explanation_graph(
        program=program,
        answer_set=answer_set,
        herbrand_base=herbrand_base,
        query=query,
    )
    print_with_title("Graph", graph)

    # show DAG
    open_graph_in_xasp_navigator(
        graph,
        with_chopped_body=True,
        with_backward_search=True,
        backward_search_symbols=(";", " :-"),
    )


if __name__ == "__main__":
    main()
