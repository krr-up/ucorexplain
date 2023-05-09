assign((Row, Col), Value) : Value=1..9  :- Row = 1..9; Col = 1..9.

% BLOCKS
% - Row-Block
block((row, Row), (Row, Col)) :- Row = 1..9, Col = 1..9.
% - Column-Block
block((col, Col), (Row, Col)) :- Row = 1..9, Col = 1..9.
% - Subgrid-Block
block((sub, Row', Col'), (Row, Col)) :- Row = 1..9; Col = 1..9; Row' = (Row-1) / 3; Col' = (Col-1) / 3.

% CONSTRAINTS
:- given(Cell, Value), not assign(Cell, Value).
:- block(Block, Cell); block(Block, Cell'), Cell != Cell'; assign(Cell, Value), assign(Cell', Value).