"""
The main entry point for the application.
"""

from dumbo_asp.primitives import (
    GroundAtom,
    Model,
    SymbolicAtom,
    SymbolicProgram,
    SymbolicRule,
)

from ucorexplain import (
    get_answer_set,
    get_mus_program_and_selectors,
    print_with_title,
    program_from_files,
    MUS_PREDICATE,
    build_extended_program_and_possible_selectors,
    get_selectors,
    remove_false,
    get_serialization_program,
    get_reified_program,
    get_derivation_sequence_program,
    get_graph
)

from .meta import run_meta
from .utils.parser import get_parser
from dumbo_asp.queries import open_graph_in_xasp_navigator


def main():
    """
    Run the main function.
    """
    parser = get_parser()
    args = parser.parse_args()

    # Program
    program = program_from_files([f.name for f in args.prg])
    print_with_title("INPUT PROGRAM", program)

    answer_set = get_answer_set(args.answer)

    # Query TODO extend for multiple atoms in query
    query_atom = GroundAtom.parse(args.query)

    extended_program, all_selectors = build_extended_program_and_possible_selectors(
        program, answer_set, query_atom, MUS_PREDICATE)

    selectors = get_selectors(extended_program, MUS_PREDICATE, all_selectors)
    selectors_prg = SymbolicProgram.parse(Model.of_atoms(selectors).as_facts)

    # Remove __false__ from rules
    extended_program = remove_false(extended_program)
    expanded_prg_with_selectors = SymbolicProgram.of(*extended_program, *selectors_prg)

    # Ground program manually
    expanded_prg = expanded_prg_with_selectors.expand_global_and_local_variables()

    # Serialize
    serialization_program = get_serialization_program(expanded_prg, query_atom)

    # Reify
    reified_program = get_reified_program(serialization_program)

    # Get derivation
    derivation_sequence = get_derivation_sequence_program(reified_program)
    # WARNING! Here I'm assuming that atoms are ordered according to the derivation in the solver. If it is not, we need a propagator or something different

    # Get graph
    graph = get_graph(derivation_sequence, serialization_program)

    # Show graph
    open_graph_in_xasp_navigator(graph)

if __name__ == "__main__":
    main()
