"""
The main entry point for the application.
"""

from dumbo_asp.primitives import SymbolicAtom, SymbolicProgram, Model, GroundAtom, SymbolicRule

from ucorexplain import get_mus_program, print_output, move_up, program_from_files, print_explanation, print_selectors, MUS_PREDICATE, build_extended_program_and_possible_selectors, get_selectors, print_with_title
from .utils.parser import get_parser
from .meta import run_meta


def main():
    """
    Run the main function.
    """
    parser = get_parser()
    args = parser.parse_args()

    # Program
    program = program_from_files([f.name for f in args.prg])
    print_with_title("INPUT PROGRAM", program)

    # Answer
    answer_set = []
    if args.answer:
        for atom in args.answer.split(' '):
            answer_set.append(
                (GroundAtom.parse(atom[1:]), False) if atom.startswith('~') else (GroundAtom.parse(atom), True)
            )

    atoms_in_answer_set = set(element[0] for element in answer_set)
    # Query TODO extend for multiple atoms in query
    query_atom = GroundAtom.parse(args.query)

    # Get full herbrand based on query and answe
    known_atoms = set(list(atoms_in_answer_set) + [query_atom])
    choices = [SymbolicRule.parse("{"+str(a)+"}.") for a in known_atoms]
    print_with_title("CHOICES", choices)
    program_with_choices = SymbolicProgram.parse(str(program) + "\n" + "".join([str(c)+"\n" for c in choices]))
    herbrand = program_with_choices.herbrand_base
    print_with_title("HERBRAND BASE", herbrand)
    herbrand_as_externals = "\n"+"\n".join(f"#external {str(h)}." for h in herbrand)

    # Add atoms from herbrand to answer set
    for atom in herbrand:
        if atom not in atoms_in_answer_set:
            answer_set.append((atom, False))
    
    # Get MUS program
    extended_program, all_selectors = build_extended_program_and_possible_selectors(
        program, answer_set, query_atom, MUS_PREDICATE
    )
    
    extended_program_with_externals = str(extended_program) + herbrand_as_externals
    print_with_title("EXTENDED PROGRAM WITH EXTERNALS", extended_program_with_externals)
    selectors = get_selectors(extended_program_with_externals, MUS_PREDICATE, all_selectors)
    print_with_title("SELECTORS",selectors)

    # TODO
    # Get transforemed extended_program_with_externals and pass this to run meta

    
    # RUN meta 
    explanation = run_meta(extended_program_with_externals,selectors, i=args.interval)
    print_with_title("EXPLANATION",explanation)





if __name__ == "__main__":
    main()
