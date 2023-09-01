"""
The main entry point for the application.
"""

from dumbo_asp.primitives import SymbolicAtom, SymbolicProgram, Model, GroundAtom, SymbolicRule

from ucorexplain import program_from_files, get_mus_program_and_selectors, print_with_title, get_answer_set
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

    answer_set = get_answer_set(args.answer)

    # Query TODO extend for multiple atoms in query
    query_atom = GroundAtom.parse(args.query)

    extended_program_with_externals, selectors = get_mus_program_and_selectors(program, answer_set, query_atom)
    
    # TODO
    # Get transforemed extended_program_with_externals and pass this to run meta

    # RUN meta 
    explanation = run_meta(extended_program_with_externals,selectors, i=args.interval)





if __name__ == "__main__":
    main()
