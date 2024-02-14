head_bounds(Rule, LowerBound, UpperBound) :-
  rule(Rule), choice(Rule, LowerBound, UpperBound).
head_bounds(Rule, 1, Size) :-
  rule(Rule), not choice(Rule,_,_);
  Size = #count{HeadAtom : head(Rule, HeadAtom)}.

atom(Atom) :- head(Rule, Atom).
atom(Atom) :- pos_body(Rule, Atom).
atom(Atom) :- neg_body(Rule, Atom).

assign'(HeadAtom, true, (support, Rule)) :-
  rule(Rule), head_bounds(Rule, LowerBound, UpperBound);
  head(Rule, HeadAtom), #sum{1, Atom : head(Rule, Atom); -1, Atom : head(Rule, Atom), assign(Atom, false, _)} = LowerBound;
  assign(BodyAtom, true, _) : pos_body(Rule, BodyAtom);
  assign(BodyAtom, false, _) : neg_body(Rule, BodyAtom).

assign'(HeadAtom, false, (head_upper_bound, Rule)) :-
  rule(Rule), head_bounds(Rule, LowerBound, UpperBound);
  head(Rule, HeadAtom), #count{Atom : head(Rule, Atom), assign(Atom, true, _), Atom != HeadAtom} = UpperBound;
  assign(BodyAtom, true, _) : pos_body(Rule, BodyAtom);
  assign(BodyAtom, false, _) : neg_body(Rule, BodyAtom).

cannot_support(Rule, HeadAtom, OtherHeadAtom) :-
  rule(Rule), head(Rule, HeadAtom), not choice(Rule,_,_);
  head(Rule, OtherHeadAtom), OtherHeadAtom != HeadAtom, assign(OtherHeadAtom, true, _).
cannot_support(Rule, HeadAtom, BodyAtom) :-
  rule(Rule), head(Rule, HeadAtom);
  pos_body(Rule, BodyAtom), assign(BodyAtom, false, _).
cannot_support(Rule, HeadAtom, BodyAtom) :-
  rule(Rule), head(Rule, HeadAtom);
  neg_body(Rule, BodyAtom), assign(BodyAtom, true, _).

assign'(Atom, false, (lack_of_support,)) :-
  atom(Atom);
  cannot_support(Rule, Atom, _) : head(Rule, Atom).

last_support(Rule, Atom) :-
  assign(Atom, true, _), head(Rule, Atom);
  cannot_support(Rule', Atom, _) : head(Rule', Atom), Rule' != Rule.
  
assign'(BodyAtom, true, (last_support, Rule, Atom)) :-
  last_support(Rule, Atom);
  pos_body(Rule, BodyAtom).
assign'(BodyAtom, false, (last_support, Rule, Atom)) :-
  last_support(Rule, Atom);
  neg_body(Rule, BodyAtom).
assign'(HeadAtom, false, (last_support, Rule, Atom)) :-
  last_support(Rule, Atom), not choice(Rule, _, _);
  head(Rule, HeadAtom), HeadAtom != Atom.

constraint(Rule, upper_bound) :-
  rule(Rule), head_bounds(Rule, LowerBound, UpperBound);
  #count{Atom : head(Rule, Atom), assign(Atom, true, _)} > UpperBound.
constraint(Rule, lower_bound) :-
  rule(Rule), head_bounds(Rule, LowerBound, UpperBound);
  #sum{1, Atom : head(Rule, Atom); -1, Atom : head(Rule, Atom), assign(Atom, false, _)} < LowerBound.

assign'(Atom, false, (constraint, Rule, Bound)) :-
  constraint(Rule, Bound), pos_body(Rule, Atom);
  assign(Atom', true, _) : pos_body(Rule, Atom'), Atom' != Atom;
  assign(Atom', false, _) : neg_body(Rule,Atom').
assign'(Atom, true, (constraint, Rule, Bound)) :-
  constraint(Rule, Bound), neg_body(Rule, Atom);
  assign(Atom', true, _) : pos_body(Rule, Atom');
  assign(Atom', false, _) : neg_body(Rule,Atom'), Atom' != Atom.
  
#show.
#show assign(Atom, Value, Reason) : assign'(Atom, Value, Reason), not assign(Atom, _, _).
#show cannot_support/3.
#show constraint/2.
#show done : #count{Atom : query(Atom), not assign'(Atom, _, _)} == 0.
