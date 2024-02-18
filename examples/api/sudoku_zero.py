from dumbo_asp.queries import open_graph_in_xasp_navigator, explanation_graph

from ucorexplain import *

program = program_from_files(["examples/sudoku/instance4x4.lp", "examples/sudoku/encoding4x4.lp"])

# the answer set contains only the atoms assigned true
answer_set = Model.of_program(program)

# the query is a set of atoms (assignment implicit from the answer set)
query = Model.of_atoms("assign((1,2),2)")

# other (false) atoms that the user want to include (if any)
explicitly_mentioned_atoms = Model.of_atoms()

# we expand the HB by disabling fact simplifications
herbrand_base = program.to_zero_simplification_version(
    extra_atoms=(*answer_set, *query, *explicitly_mentioned_atoms),
    compact=True,
).herbrand_base_without_false_predicate

# LET USERS EXPAND THE VARIABLES THEY LIKE AND REORDER THE PROGRAM AS THEY WISH
program = program.expand_global_safe_variables(rule=program[-5], variables=["Block"], herbrand_base=herbrand_base)
program = program.move_up(SymbolicAtom.parse("block(Block, Cell)"))

# possibly move_up also on the herbrand_base
herbrand_base = SymbolicProgram.parse(herbrand_base.as_facts)  # temporary switch to a program (of facts)
herbrand_base = herbrand_base.move_up(SymbolicAtom.parse("assign((Row,Col), 2)"))
herbrand_base = herbrand_base.move_up(SymbolicAtom.parse("assign((1,Col), 2)"))
herbrand_base = herbrand_base.move_up(SymbolicAtom.parse("assign((Row,2), 2)"))  # this is the second most important
herbrand_base = herbrand_base.move_up(SymbolicAtom.parse("assign((1,2), 2)"))   # this is the most important
herbrand_base = tuple(GroundAtom.parse(str(rule.head_atom)) for rule in herbrand_base)  # back to an iterable of GroundAtoms

# compute DAG
graph = explanation_graph(
    program=program,
    answer_set=answer_set,
    herbrand_base=herbrand_base,
    query=query,
)

# show DAG
open_graph_in_xasp_navigator(graph, with_chopped_body=True, with_backward_search=True,
                             backward_search_symbols=(';', ' :-'))
