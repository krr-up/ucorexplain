% %%%%%%%%%%%%%%%%%%%%%%%%% Visualization
graph(sudoku).

% Name of graph
attr(graph, sudoku, name, "Sudoku").

% Global graph attributes
attr(graph, sudoku, nodesep, 1).
attr(graph, sudoku, newrank, true).

% Global node attributes
attr(graph_nodes, sudoku, shape, square).
attr(graph_nodes, sudoku, style, filled).
attr(graph_nodes, sudoku, fillcolor, white).
attr(graph_nodes, sudoku, width, "1").
attr(graph_nodes, sudoku, fontsize, 30).

% Nodes
pos(1..9,1..9).
node(pos(X,Y), sudoku):- pos(X,Y).
% attr(node, pos(X,Y), fillcolor, "grey88"):- pos(X,Y), subgrid(X,Y,S), S\2==0.

attr(node, pos(X,Y), label, V):- assign((X,Y),V), not given((X,Y),_).
attr(node, pos(X,Y), label, @format("<<B>{}</B>>",V)):- given((X,Y),V).
attr(node, pos(X,Y), fontcolor, gray):- assign((X,Y),V), not given((X,Y),_).
attr(node, pos(X,Y), pos, @pos(X,Y)):- pos(X,Y).