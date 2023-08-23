"""
The main entry point for the application.
"""

from dumbo_asp.primitives import SymbolicAtom, SymbolicProgram, Model, GroundAtom

from ucorexplain import get_mus_program, print_output, move_up, program_from_files, print_explanation, print_selectors
from .utils.parser import get_parser
from .meta import run_meta

def main():
    """
    Run the main function.
    """
    parser = get_parser()
    args = parser.parse_args()

    # Program
    the_program = program_from_files([f.name for f in args.prg])

    # Answer
    the_answer_set = []
    if args.answer:
        for atom in args.answer.split(' '):
            the_answer_set.append(
                (GroundAtom.parse(atom[1:]), False) if atom.startswith('~') else (GroundAtom.parse(atom), True)
            )

    atoms_in_the_answer_set = set(element[0] for element in the_answer_set)
    for atom in the_program.herbrand_base:
        if atom not in atoms_in_the_answer_set:
            the_answer_set.append((atom, False))

    # Query
    query_atom = GroundAtom.parse(args.query)
    mus_prg, selectors = get_mus_program(
        program=the_program,
        answer_set=tuple(the_answer_set),
        query_atom=query_atom,
        use_core=True
    )
    
    # Get MUS program
    print_output(query_atom, mus_prg)
    print_selectors(selectors)
    
    # RUN meta 
    explanation = run_meta(mus_prg,selectors, i=args.interval)
    print_explanation(explanation)





if __name__ == "__main__":
    main()
