from dumbo_asp.primitives import SymbolicAtom, SymbolicProgram, Model, GroundAtom

from ucorexplain import extend_answer_set, get_selectors, remove_false, build_extended_program_and_possible_selectors, print_output, move_up, program_from_files, print_selectors, MUS_PREDICATE, get_herbrand_zero

program = program_from_files(["examples/sudoku/instance4x4.lp","examples/sudoku/encoding4x4.lp"])

atoms_in_answer_set = Model.of_program(program).filter(when=lambda atom: atom.predicate_name == 'assign')
print(atoms_in_answer_set)
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

# Remove __false__ from rules
extended_program = remove_false(extended_program)


# ------------ Tested until here




expanded_prg = extended_program.expand_global_and_local_variables()

# Error
serialized = expanded_prg.serialize(base64_encode=False)

# ------- Next steps
# Call mario_reify together with the query 

# Call mario_meta with the reiified encoding