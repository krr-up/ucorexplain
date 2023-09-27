link(Atom, BodyAtom) :-
  assign(Atom, _, (support, Rule), _);
  pos_body(Rule, BodyAtom).
link(Atom, BodyAtom) :-
  assign(Atom, _, (support, Rule), _);
  neg_body(Rule, BodyAtom).
link(Atom, HeadAtom) :-
  assign(Atom, _, (support, Rule), _);
  head(Rule, HeadAtom), assign(HeadAtom, false, _, _).

link(Atom, BodyAtom) :-
  assign(Atom, _, (choice, Rule), _);
  pos_body(Rule, BodyAtom).
link(Atom, BodyAtom) :-
  assign(Atom, _, (choice, Rule), _);
  neg_body(Rule, BodyAtom).
link(Atom, HeadAtom) :-
  assign(Atom, _, (choice, Rule), Index);
  head(Rule, HeadAtom), assign(HeadAtom, true, _, Index'), Index' < Index.

{link(Atom, Atom'): false_body(Rule, Atom', Index'), Index' < Index} = 1 :-
  assign(Atom, _, (lack_of_support,), Index);
  head(Rule, Atom).
  % disj rule?

%link(HeadAtom, Atom) :-
%  assign(Atom, _, (last_support, Rule, Atom), Index);
%  head(Rule, HeadAtom), assign(HeadAtom, _, _, Index'), Index' < Index.
% handle disjunctive rules?
link(BodyAtom, Atom) :-
  assign(BodyAtom, _, (last_support, Rule, Atom), _).
{link(BodyAtom, Atom'): false_body(Rule', Atom', Index'), Index' < Index} = 1 :-
  assign(BodyAtom, _, (last_support, Rule, Atom), Index);
  head(Rule', Atom), false_body(Rule, Atom, _).

link(Atom, HeadAtom) :-
  assign(Atom, _, (constraint, Rule), Index);
  head(Rule, HeadAtom), assign(HeadAtom, _, _, Index'), Index' < Index.
link(Atom, BodyAtom) :-
  assign(Atom, _, (constraint, Rule), _);
  pos_body(Rule, BodyAtom), BodyAtom != Atom.
link(Atom, BodyAtom) :-
  assign(Atom, _, (constraint, Rule), _);
  neg_body(Rule, BodyAtom), BodyAtom != Atom.

reach(Atom) :- query(Atom).
reach(Atom') :- reach(Atom), link(Atom, Atom'), not hide(Atom').

hide(Atom) :- head(Rule, Atom); not pos_body(Rule,_); not neg_body(Rule,_).

%#show.
%#show node(X,V,R) : assign(X,V,R,_), reach(X).
%#show link(X,Y) : link(X,Y), reach(X), reach(Y).
node(X,V,R) :- assign(X,V,R,_), reach(X).
link'(X,Y) :- link(X,Y), reach(X), reach(Y).