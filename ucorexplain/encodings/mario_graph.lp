link(Atom, BodyAtom) :-
  assign(Atom, _, (support, Rule));
  pos_body(Rule, BodyAtom).
link(Atom, BodyAtom) :-
  assign(Atom, _, (support, Rule));
  neg_body(Rule, BodyAtom).
link(Atom, FalseHeadAtom) :-
  assign(Atom, _, (support, Rule));
  head(Rule, FalseHeadAtom), assign(FalseHeadAtom, false, _).

link(Atom, BodyAtom) :-
  assign(Atom, _, (head_upper_bound, Rule));
  pos_body(Rule, BodyAtom).
link(Atom, BodyAtom) :-
  assign(Atom, _, (head_upper_bound, Rule));
  neg_body(Rule, BodyAtom).
link(Atom, TrueHeadAtom) :-
  assign(Atom, _, (head_upper_bound, Rule));
  head(Rule, TrueHeadAtom), assign(TrueHeadAtom, true, _).

link(Atom, BecauseOfAtom) :-
  assign(Atom, _, (lack_of_support,));
  head(Rule, Atom), cannot_support(Rule, Atom, BecauseOfAtom).

link(Atom, AtomToSupport) :-
  assign(Atom, _, (last_support, Rule, AtomToSupport)).
link(Atom, BecauseOfAtom) :-
  assign(Atom, _, (last_support, Rule, AtomToSupport));
  cannot_support(Rule, AtomToSupport, BecauseOfAtom).

link(Atom, TrueHeadAtom) :-
  assign(Atom, _, (constraint, Rule, upper_bound));
  head(Rule, TrueHeadAtom), assign(TrueHeadAtom, true, _).
link(Atom, FalseHeadAtom) :-
  assign(Atom, _, (constraint, Rule, lower_bound));
  head(Rule, FalseHeadAtom), assign(FalseHeadAtom, false, _).
link(Atom, BodyAtom) :-
  assign(Atom, _, (constraint, Rule, _));
  pos_body(Rule, BodyAtom), BodyAtom != Atom.
link(Atom, BodyAtom) :-
  assign(Atom, _, (constraint, Rule, _));
  neg_body(Rule, BodyAtom), BodyAtom != Atom.


reach(Atom) :- query(Atom).
reach(Atom') :- reach(Atom), link(Atom, Atom'), not hide(Atom').

hide(Atom) :- head(Rule, Atom); not pos_body(Rule,_); not neg_body(Rule,_).

#show.
#show node(X,V,R) : assign(X,V,R), reach(X).
#show link(X,Y) : link(X,Y), reach(X), reach(Y).