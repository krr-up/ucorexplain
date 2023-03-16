"""
The main entry point for the application.
"""

from dumbo_asp.primitives import SymbolicAtom, SymbolicRule, SymbolicProgram, Model, GroundAtom

from .utils.logger import setup_logger
from .utils.parser import get_parser

from . import explain, print_output

def main():
    """
    Run the main function.
    """
    program = SymbolicProgram.parse("""
    % prefer clues in the same row
    given((7, 1), 8).
    given((7, 2), 5).
    given((7, 3), 4).
    given((7, 4), 7).
    given((7, 5), 2).
    given((7, 7), 6).
    given((7, 8), 9).

    % prefer clues in the same column
    given((2, 9), 1).
    given((4, 9), 2).
    given((8, 9), 8).
    given((9, 9), 5).

    % prefer clues in the same sub-block
    given((9, 7), 7).
    given((9, 8), 1).

    given((1, 1), 6).
    given((1, 3), 9).
    given((1, 4), 8).
    given((1, 6), 7).
    given((2, 4), 6).
    given((3, 2), 3).
    given((3, 3), 5).
    given((3, 6), 2).
    given((3, 8), 7).
    given((4, 2), 6).
    given((4, 3), 8).
    given((4, 7), 1).
    given((5, 1), 3).
    given((5, 6), 5).
    given((6, 4), 2).
    given((6, 7), 3).
    given((6, 8), 6).
    given((8, 4), 5).
    given((8, 5), 9).
    given((9, 1), 2).
    given((9, 3), 6).
    given((9, 4), 4).
    given((9, 5), 3).


    {assign((Row, Col), Value) : Value = 1..9} = 1 :- Row = 1..9; Col = 1..9.
    :- block(Block, Cell); block(Block, Cell'), Cell != Cell'; assign(Cell, Value), assign(Cell', Value).
    :- given(Cell, Value), not assign(Cell, Value).
    block((row, 1), (1, Col)) :- Col = 1..9.
    block((row, 2), (2, Col)) :- Col = 1..9.
    block((row, 3), (3, Col)) :- Col = 1..9.
    block((row, 4), (4, Col)) :- Col = 1..9.
    block((row, 5), (5, Col)) :- Col = 1..9.
    block((row, 6), (6, Col)) :- Col = 1..9.
    block((row, 7), (7, Col)) :- Col = 1..9.
    block((row, 8), (8, Col)) :- Col = 1..9.
    block((row, 9), (9, Col)) :- Col = 1..9.
    block((col, 1), (Row, 1)) :- Row = 1..9.
    block((col, 2), (Row, 2)) :- Row = 1..9.
    block((col, 3), (Row, 3)) :- Row = 1..9.
    block((col, 4), (Row, 4)) :- Row = 1..9.
    block((col, 5), (Row, 5)) :- Row = 1..9.
    block((col, 6), (Row, 6)) :- Row = 1..9.
    block((col, 7), (Row, 7)) :- Row = 1..9.
    block((col, 8), (Row, 8)) :- Row = 1..9.
    block((col, 9), (Row, 9)) :- Row = 1..9.
    block((sub, 0, 0), (Row, Col)) :- Row = 1..3; Col = 1..3.
    block((sub, 0, 1), (Row, Col)) :- Row = 1..3; Col = 4..6.
    block((sub, 0, 2), (Row, Col)) :- Row = 1..3; Col = 7..9.
    block((sub, 1, 0), (Row, Col)) :- Row = 4..6; Col = 1..3.
    block((sub, 1, 1), (Row, Col)) :- Row = 4..6; Col = 4..6.
    block((sub, 1, 2), (Row, Col)) :- Row = 4..6; Col = 7..9.
    block((sub, 2, 0), (Row, Col)) :- Row = 7..9; Col = 1..3.
    block((sub, 2, 1), (Row, Col)) :- Row = 7..9; Col = 4..6.
    block((sub, 2, 2), (Row, Col)) :- Row = 7..9; Col = 7..9.
    block((sub, (Row-1) / 3, (Col-1) / 3), (Row, Col)) :- Row = 1..9; Col = 1..9.
    """)
    query_atom = GroundAtom.parse("assign((7,9),3)")
    result = explain(
        program=program,
        answer_set=Model.of_program("block((row,1),(1,1)). block((row,1),(1,2)). block((row,1),(1,3)). block((row,1),(1,4)). block((row,1),(1,5)). block((row,1),(1,6)). block((row,1),(1,7)). block((row,1),(1,8)). block((row,1),(1,9)). block((row,2),(2,1)). block((row,2),(2,2)). block((row,2),(2,3)). block((row,2),(2,4)). block((row,2),(2,5)). block((row,2),(2,6)). block((row,2),(2,7)). block((row,2),(2,8)). block((row,2),(2,9)). block((row,3),(3,1)). block((row,3),(3,2)). block((row,3),(3,3)). block((row,3),(3,4)). block((row,3),(3,5)). block((row,3),(3,6)). block((row,3),(3,7)). block((row,3),(3,8)). block((row,3),(3,9)). block((row,4),(4,1)). block((row,4),(4,2)). block((row,4),(4,3)). block((row,4),(4,4)). block((row,4),(4,5)). block((row,4),(4,6)). block((row,4),(4,7)). block((row,4),(4,8)). block((row,4),(4,9)). block((row,5),(5,1)). block((row,5),(5,2)). block((row,5),(5,3)). block((row,5),(5,4)). block((row,5),(5,5)). block((row,5),(5,6)). block((row,5),(5,7)). block((row,5),(5,8)). block((row,5),(5,9)). block((row,6),(6,1)). block((row,6),(6,2)). block((row,6),(6,3)). block((row,6),(6,4)). block((row,6),(6,5)). block((row,6),(6,6)). block((row,6),(6,7)). block((row,6),(6,8)). block((row,6),(6,9)). block((row,7),(7,1)). block((row,7),(7,2)). block((row,7),(7,3)). block((row,7),(7,4)). block((row,7),(7,5)). block((row,7),(7,6)). block((row,7),(7,7)). block((row,7),(7,8)). block((row,7),(7,9)). block((row,8),(8,1)). block((row,8),(8,2)). block((row,8),(8,3)). block((row,8),(8,4)). block((row,8),(8,5)). block((row,8),(8,6)). block((row,8),(8,7)). block((row,8),(8,8)). block((row,8),(8,9)). block((row,9),(9,1)). block((row,9),(9,2)). block((row,9),(9,3)). block((row,9),(9,4)). block((row,9),(9,5)). block((row,9),(9,6)). block((row,9),(9,7)). block((row,9),(9,8)). block((row,9),(9,9)). block((col,1),(1,1)). block((col,2),(1,2)). block((col,3),(1,3)). block((col,4),(1,4)). block((col,5),(1,5)). block((col,6),(1,6)). block((col,7),(1,7)). block((col,8),(1,8)). block((col,9),(1,9)). block((col,1),(2,1)). block((col,2),(2,2)). block((col,3),(2,3)). block((col,4),(2,4)). block((col,5),(2,5)). block((col,6),(2,6)). block((col,7),(2,7)). block((col,8),(2,8)). block((col,9),(2,9)). block((col,1),(3,1)). block((col,2),(3,2)). block((col,3),(3,3)). block((col,4),(3,4)). block((col,5),(3,5)). block((col,6),(3,6)). block((col,7),(3,7)). block((col,8),(3,8)). block((col,9),(3,9)). block((col,1),(4,1)). block((col,2),(4,2)). block((col,3),(4,3)). block((col,4),(4,4)). block((col,5),(4,5)). block((col,6),(4,6)). block((col,7),(4,7)). block((col,8),(4,8)). block((col,9),(4,9)). block((col,1),(5,1)). block((col,2),(5,2)). block((col,3),(5,3)). block((col,4),(5,4)). block((col,5),(5,5)). block((col,6),(5,6)). block((col,7),(5,7)). block((col,8),(5,8)). block((col,9),(5,9)). block((col,1),(6,1)). block((col,2),(6,2)). block((col,3),(6,3)). block((col,4),(6,4)). block((col,5),(6,5)). block((col,6),(6,6)). block((col,7),(6,7)). block((col,8),(6,8)). block((col,9),(6,9)). block((col,1),(7,1)). block((col,2),(7,2)). block((col,3),(7,3)). block((col,4),(7,4)). block((col,5),(7,5)). block((col,6),(7,6)). block((col,7),(7,7)). block((col,8),(7,8)). block((col,9),(7,9)). block((col,1),(8,1)). block((col,2),(8,2)). block((col,3),(8,3)). block((col,4),(8,4)). block((col,5),(8,5)). block((col,6),(8,6)). block((col,7),(8,7)). block((col,8),(8,8)). block((col,9),(8,9)). block((col,1),(9,1)). block((col,2),(9,2)). block((col,3),(9,3)). block((col,4),(9,4)). block((col,5),(9,5)). block((col,6),(9,6)). block((col,7),(9,7)). block((col,8),(9,8)). block((col,9),(9,9)). block((sub,0,0),(1,1)). block((sub,0,0),(1,2)). block((sub,0,0),(1,3)). block((sub,0,1),(1,4)). block((sub,0,1),(1,5)). block((sub,0,1),(1,6)). block((sub,0,2),(1,7)). block((sub,0,2),(1,8)). block((sub,0,2),(1,9)). block((sub,0,0),(2,1)). block((sub,0,0),(2,2)). block((sub,0,0),(2,3)). block((sub,0,1),(2,4)). block((sub,0,1),(2,5)). block((sub,0,1),(2,6)). block((sub,0,2),(2,7)). block((sub,0,2),(2,8)). block((sub,0,2),(2,9)). block((sub,0,0),(3,1)). block((sub,0,0),(3,2)). block((sub,0,0),(3,3)). block((sub,0,1),(3,4)). block((sub,0,1),(3,5)). block((sub,0,1),(3,6)). block((sub,0,2),(3,7)). block((sub,0,2),(3,8)). block((sub,0,2),(3,9)). block((sub,1,0),(4,1)). block((sub,1,0),(4,2)). block((sub,1,0),(4,3)). block((sub,1,1),(4,4)). block((sub,1,1),(4,5)). block((sub,1,1),(4,6)). block((sub,1,2),(4,7)). block((sub,1,2),(4,8)). block((sub,1,2),(4,9)). block((sub,1,0),(5,1)). block((sub,1,0),(5,2)). block((sub,1,0),(5,3)). block((sub,1,1),(5,4)). block((sub,1,1),(5,5)). block((sub,1,1),(5,6)). block((sub,1,2),(5,7)). block((sub,1,2),(5,8)). block((sub,1,2),(5,9)). block((sub,1,0),(6,1)). block((sub,1,0),(6,2)). block((sub,1,0),(6,3)). block((sub,1,1),(6,4)). block((sub,1,1),(6,5)). block((sub,1,1),(6,6)). block((sub,1,2),(6,7)). block((sub,1,2),(6,8)). block((sub,1,2),(6,9)). block((sub,2,0),(7,1)). block((sub,2,0),(7,2)). block((sub,2,0),(7,3)). block((sub,2,1),(7,4)). block((sub,2,1),(7,5)). block((sub,2,1),(7,6)). block((sub,2,2),(7,7)). block((sub,2,2),(7,8)). block((sub,2,2),(7,9)). block((sub,2,0),(8,1)). block((sub,2,0),(8,2)). block((sub,2,0),(8,3)). block((sub,2,1),(8,4)). block((sub,2,1),(8,5)). block((sub,2,1),(8,6)). block((sub,2,2),(8,7)). block((sub,2,2),(8,8)). block((sub,2,2),(8,9)). block((sub,2,0),(9,1)). block((sub,2,0),(9,2)). block((sub,2,0),(9,3)). block((sub,2,1),(9,4)). block((sub,2,1),(9,5)). block((sub,2,1),(9,6)). block((sub,2,2),(9,7)). block((sub,2,2),(9,8)). block((sub,2,2),(9,9)). given((1,1),6). given((1,3),9). given((1,4),8). given((1,6),7). given((2,4),6). given((2,9),1). given((3,2),3). given((3,3),5). given((3,6),2). given((3,8),7). given((4,2),6). given((4,3),8). given((4,7),1). given((4,9),2). given((5,1),3). given((5,6),5). given((6,4),2). given((6,7),3). given((6,8),6). given((7,1),8). given((7,2),5). given((7,3),4). given((7,4),7). given((7,5),2). given((7,7),6). given((7,8),9). given((8,4),5). given((8,5),9). given((8,9),8). given((9,1),2). given((9,3),6). given((9,4),4). given((9,5),3). given((9,7),7). given((9,8),1). given((9,9),5). assign((1,1),6). assign((1,3),9). assign((1,4),8). assign((1,6),7). assign((2,4),6). assign((2,9),1). assign((3,2),3). assign((3,3),5). assign((3,6),2). assign((3,8),7). assign((4,2),6). assign((4,3),8). assign((4,7),1). assign((4,9),2). assign((5,1),3). assign((5,6),5). assign((6,4),2). assign((6,7),3). assign((6,8),6). assign((7,1),8). assign((7,2),5). assign((7,3),4). assign((7,4),7). assign((7,5),2). assign((7,7),6). assign((7,8),9). assign((8,4),5). assign((8,5),9). assign((8,9),8). assign((9,1),2). assign((9,3),6). assign((9,4),4). assign((9,5),3). assign((9,7),7). assign((9,8),1). assign((9,9),5). assign((1,5),1). assign((1,2),2). assign((1,8),3). assign((1,9),4). assign((1,7),5). assign((2,8),2). assign((2,6),3). assign((2,1),4). assign((2,5),5). assign((2,3),7). assign((2,2),8). assign((2,7),9). assign((3,1),1). assign((3,5),4). assign((3,9),6). assign((3,7),8). assign((3,4),9). assign((4,4),3). assign((4,6),4). assign((4,8),5). assign((4,5),7). assign((4,1),9). assign((5,4),1). assign((5,3),2). assign((5,7),4). assign((5,5),6). assign((5,2),7). assign((5,8),8). assign((5,9),9). assign((6,3),1). assign((6,2),4). assign((6,1),5). assign((6,9),7). assign((6,5),8). assign((6,6),9). assign((7,6),1). assign((7,9),3). assign((8,2),1). assign((8,7),2). assign((8,3),3). assign((8,8),4). assign((8,6),6). assign((8,1),7). assign((9,6),8). assign((9,2),9)."),
        query_atom=query_atom,
        priority_list=tuple(GroundAtom.parse(atom) for atom in [
            "assign((7,1),8)",
            "assign((7,2),5)",
            "assign((7,3),4)",
            "assign((7,4),7)",
            "assign((7,5),2)",
            "assign((7,7),6)",
            "assign((7,8),9)",

            "assign((2,9),1)",
            "assign((4,9),2)",
            "assign((8,9),8)",
            "assign((1,9),4)",
            "assign((9,9),5)",
            "assign((3,9),6)",
            "assign((5,9),9)",
            "assign((6,9),7)",
            "assign((7,9),3)",

            "assign((1,4),8)",
            "assign((1,6),7)",
            "assign((2,4),6)",
            "assign((3,2),3)",
            "assign((3,3),5)",
            "assign((3,6),2)",
            "assign((3,8),7)",
            "assign((4,2),6)",
            "assign((4,3),8)",
            "assign((4,7),1)",
            "assign((5,1),3)",
            "assign((5,6),5)",
            "assign((6,4),2)",
            "assign((6,7),3)",
            "assign((6,8),6)",
            "assign((8,4),5)",
            "assign((8,5),9)",
            "assign((9,1),2)",
            "assign((9,3),6)",
            "assign((9,4),4)",
            "assign((9,5),3)",
            "assign((9,7),7)",
            "assign((9,8),1)",
            "assign((1,5),1)",
            "assign((1,2),2)",
            "assign((1,8),3)",
            "assign((1,7),5)",
            "assign((2,8),2)",
            "assign((2,6),3)",
            "assign((2,1),4)",
            "assign((2,5),5)",
            "assign((2,3),7)",
            "assign((2,2),8)",
            "assign((2,7),9)",
            "assign((3,1),1)",
            "assign((3,5),4)",
            "assign((3,7),8)",
            "assign((3,4),9)",
            "assign((4,4),3)",
            "assign((4,6),4)",
            "assign((4,8),5)",
            "assign((4,5),7)",
            "assign((4,1),9)",
            "assign((5,4),1)",
            "assign((5,3),2)",
            "assign((5,7),4)",
            "assign((5,5),6)",
            "assign((5,2),7)",
            "assign((5,8),8)",
            "assign((6,3),1)",
            "assign((6,2),4)",
            "assign((6,1),5)",
            "assign((6,5),8)",
            "assign((6,6),9)",
            "assign((7,6),1)",
            "assign((8,2),1)",
            "assign((8,7),2)",
            "assign((8,3),3)",
            "assign((8,8),4)",
            "assign((8,6),6)",
            "assign((8,1),7)",
            "assign((9,6),8)",
            "assign((9,2),9)",
        ]),
    )
    print_output(query_atom, result)


if __name__ == "__main__":
    main()