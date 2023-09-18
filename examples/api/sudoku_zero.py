import clingo
from dumbo_asp.primitives import SymbolicAtom, SymbolicProgram, Model, GroundAtom

from ucorexplain import extend_answer_set, get_selectors, remove_false, build_extended_program_and_possible_selectors, print_output, move_up, program_from_files, print_selectors, MUS_PREDICATE, get_herbrand_zero

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

# Remove __false__ from rules
extended_program = remove_false(extended_program)


# Ground program manually
expanded_prg = extended_program.expand_global_and_local_variables()

# Reify
expanded_prg_facts = Model.of_atoms(expanded_prg.serialize(base64_encode=False)).as_facts
expanded_prg_program = SymbolicProgram.parse(expanded_prg_facts)
reify_program = program_from_files(["ucorexplain/encodings/mario_reify.lp"])
query_program = SymbolicProgram.parse(f"query({query_atom}).")
full_program = SymbolicProgram.of(*reify_program, *expanded_prg_program, *query_program)
reified_program = Model.of_program(full_program).as_facts

# Get derivation
derivation_sequence = []
ctl = clingo.Control(["1"])
ctl.load("ucorexplain/encodings/mario_meta.lp")
ctl.add("base",[],reified_program)
ctl.ground([("base", [])])
def m(atoms):
    print("model")
    for atom in atoms.symbols(shown=True):
        at = GroundAtom.parse(str(atom))
        derivation_sequence.append(f"{at.predicate_name}({','.join(str(arg) for arg in at.arguments)},{len(derivation_sequence) + 1})")
ctl.solve(on_model=m)
derivation_sequence = Model.of_atoms(derivation_sequence)