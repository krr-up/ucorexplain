
#script (python)
from clingo.symbol import String
import base64

def fromb64(s):
    s = str(s)
    decoded = base64.b64decode(s).decode('ascii')
    return String(decoded)

#end.
node_rule(X,R):-input_node(X,_,(_,R,_)).
node_rule(X,R):-input_node(X,_,(_,R)).
node_rule(X,""):-input_node(X,_,(_)), not input_node(X,_,(_,_)), not input_node(X,_,(_,_,_)).
node_reason(X,@concat(R," (",R',")")):-input_node(X,_,(R,_,R')).
node_reason(X,R):-input_node(X,_,(R,_)).
node_reason(X,R):-input_node(X,_,(R)), not input_node(X,_,(_,_)), not input_node(X,_,(_,_,_)).

node(X):-input_node(X,_,_).
attr(node,X, style, filled):-input_node(X,_,_).
attr(node,X, shape, plain):-input_node(X,_,_).
attr(node, X, fillcolor, @color(red,70)):-input_node(X,false,_).
attr(node, X, fillcolor, @color(green,70)):-input_node(X,true,_).
attr(node, X, label, @concat(
    "<<TABLE cellborder='1' border='{{border}}' cellspacing='0'>",
    "<TR><TD><b>{{name}}</b></TD></TR>",
    "<TR><TD><i>{{reason}}</i><br/>",
        "<FONT face='monospace'>{{rule}}</FONT></TD></TR>",
    "</TABLE>>")):-input_node(X,_,_).
attr(node, X, (label,reason), R):-node_reason(X,R).
attr(node, X, (label,rule),@fromb64(R)):-node_rule(X,R).
attr(node, X, (label,name), X):-input_node(X,_,_).
attr(node, X, (label,border), 0):-input_node(X,_,_), input_link(X,Y,_), Y!=X.
attr(node, X, (label,border), 2):-input_node(X,_,_), #false: input_link(X,Y,_), Y!=X.
edge((X,Y)):-input_link(X,Y,_),X!=Y.
attr(edge,(X,Y),label,"<<FONT face='monospace'>{{rule}}</FONT>>"):-input_link(X,Y,R),X!=Y, not node_rule(X,R).
attr(edge,(X,Y),(label,rule), @fromb64(R)):-input_link(X,Y,R),X!=Y, not node_rule(X,R).


linked_element(node,Y,X):-input_link(X,Y,_).
linked_element(node,X,X):-input_node(X,_,_).
linked_element(edge,(X,Y),X):-input_link(X,Y,_),edge((X,Y)).

% SVG interaction
root(X):- input_node(X,_,_), #count{Y: input_node(Y,_,_), input_link(Y,X,_), Y!=X}=0.
attr(node,X,class,@svg_init("visibility","hidden")):-input_node(X,_,_), not root(X).
attr(edge,E,class,@svg_init("visibility","hidden")):-edge(E).

attr(Type,E,class,@svg("click",X,"visibility","visible")):-linked_element(Type,E,X).
attr(Type,E,class,@svg("mouseenter",X,"opacity","1")):-linked_element(Type,E,X).
attr(Type,E,class,@svg("mouseleave",X,"opacity","0.3")):-linked_element(Type,E,X).
