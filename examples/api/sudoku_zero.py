# import clingo
# from dumbo_asp.primitives import SymbolicAtom, SymbolicProgram, Model, GroundAtom, Predicate

from dumbo_asp.queries import open_graph_in_xasp_navigator

from ucorexplain import *

program = program_from_files(["examples/sudoku/instance4x4.lp","examples/sudoku/encoding4x4.lp"])

atoms_in_answer_set = Model.of_program(program).filter(when=lambda atom: atom.predicate_name == 'assign')
answer_set = tuple([tuple([a,True]) for a in atoms_in_answer_set])

#print(model.as_facts)
#assert False
query_atom = GroundAtom.parse("assign((1,2),2)")

herbrand_base = get_herbrand_zero(program, atoms_in_answer_set)


# Add atoms from herbrand to answer set
answer_set = extend_answer_set(answer_set, herbrand_base)

# LET USERS EXPAND THE VARIABLES THEY LIKE AND REORDER THE PROGRAM AS THEY WISH
program = program.expand_global_safe_variables(rule=program[-5], variables=["Block"], herbrand_base=herbrand_base)
program = program.move_up(SymbolicAtom.parse("block(Block, Cell)"))

# Get MUS program
extended_program, all_selectors = build_extended_program_and_possible_selectors(
    program, answer_set, query_atom, MUS_PREDICATE
)

selectors = get_selectors(
    extended_program, MUS_PREDICATE, all_selectors
)
selectors_prg = SymbolicProgram.parse(Model.of_atoms(selectors).as_facts)

# Remove __false__ from rules
extended_program = remove_false(extended_program)
expanded_prg_with_selectors = SymbolicProgram.of(*extended_program, *selectors_prg)

# Ground program manually
expanded_prg = expanded_prg_with_selectors.expand_global_and_local_variables()

# Serialize
serialization_program  = get_serialization_program(expanded_prg, query_atom)

# Reify
reified_program = get_reified_program(serialization_program)

# Get derivation
derivation_sequence = get_derivation_sequence_program(reified_program)
# WARNING! Here I'm assuming that atoms are ordered according to the derivation in the solver. If it is not, we need a propagator or something different

# Get graph
graph = get_graph(derivation_sequence, serialization_program)

# Show graph
open_graph_in_xasp_navigator(graph)