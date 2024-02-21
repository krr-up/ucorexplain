
#script (python)
from clingo.symbol import String
import base64

def fromb64(s):
    s = str(s).strip('"')
    decoded = base64.b64decode(s).decode('utf-8')
    pos = decoded.find("__pus")
    decoded = decoded[1:pos]+"."
    return String(decoded)

#end.
viz_node(X):-node(X,_,_).
viz_attr(node,X, style, filled):-node(X,_,_).
viz_attr(node,X, shape, plain):-node(X,_,_).
viz_attr(node, X, fillcolor, @color(red,70)):-node(X,false,_).
viz_attr(node, X, fillcolor, @color(green,70)):-node(X,true,_).
viz_attr(node, X, label, @concat(
    "<<TABLE cellborder='1' border='0' cellspacing='0'>",
    "<TR><TD><b>{{name}}</b></TD></TR>",
    "<TR><TD><i>{{reason}}</i><br/>{{rule}}</TD></TR>",
    "</TABLE>>")):-node(X,_,_).
viz_attr(node, X, (label,reason),@concat(R," (", R',")")):-node(X,_,(R,_,R')).
viz_attr(node, X, (label,reason), R):-node(X,_,(R,_)).
viz_attr(node, X, (label,reason), R):-node(X,_,(R)), not node(X,_,(_,_)), not node(X,_,(_,_,_)).
viz_attr(node, X, (label,rule),@fromb64(R)):-node(X,_,(_,R,_)).
viz_attr(node, X, (label,rule), @fromb64(R)):-node(X,_,(_,R)).
viz_attr(node, X, (label,rule), ""):- node(X,_,(_)), not node(X,_,(_,_)), not node(X,_,(_,_,_)).
viz_attr(node, X, (label,name), X):-node(X,_,_).
viz_edge((X,Y)):-link(X,Y,_).