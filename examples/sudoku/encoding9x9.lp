{assign((Row, Col), Value) : Value = 1..9} = 1 :- Row = 1..9; Col = 1..9.
:- block(Block, Cell); block(Block, Cell'), Cell != Cell'; assign(Cell, Value), assign(Cell', Value).
:- given(Cell, Value), not assign(Cell, Value).
% :- block(Block, Cell'); Value = 1..9; not assign(Cell, Value) : block(Block, Cell).

block((row, Row), (Row, Col)) :- Row = 1..9, Col = 1..9.
block((col, Col), (Row, Col)) :- Row = 1..9, Col = 1..9.
block((sub, Row', Col'), (Row, Col)) :- Row = 1..9; Col = 1..9; Row' = (Row-1) / 3; Col' = (Col-1) / 3.