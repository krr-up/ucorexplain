:- atom(Atom), #count{Value, Reason : assign(Atom, Value, Reason)} > 1.
:- query(Atom), not assign(Atom, _, _).

{assign(HeadAtom, true, (support, Rule))} :-
  rule(Rule), head_bounds(Rule, LowerBound, UpperBound);
  head(Rule, HeadAtom), #sum{1, Atom : head(Rule, Atom); -1, Atom : head(Rule, Atom), assign(Atom, false, _)} = LowerBound;
  assign(BodyAtom, true, _) : pos_body(Rule, BodyAtom);
  assign(BodyAtom, false, _) : neg_body(Rule, BodyAtom).

{assign(HeadAtom, false, (choice, Rule))} :-
  rule(Rule), head_bounds(Rule, LowerBound, UpperBound);
  head(Rule, HeadAtom), #count{Atom : head(Rule, Atom), assign(Atom, true, _), Atom != HeadAtom} = UpperBound;
  assign(BodyAtom, true, _) : pos_body(Rule, BodyAtom);
  assign(BodyAtom, false, _) : neg_body(Rule, BodyAtom).

false_body(Rule, Atom) :-
  rule(Rule), pos_body(Rule, Atom), assign(Atom, false, _).
false_body(Rule, Atom) :-
  rule(Rule), neg_body(Rule, Atom), assign(Atom, true, _).

{assign(Atom, false, (lack_of_support,))} :-
  atom(Atom);
  false_body(Rule, _) : head(Rule, Atom).

last_support(Rule, Atom) :-
  assign(Atom, true, _), head(Rule, Atom);
  #count{Rule' : head(Rule', Atom), not false_body(Rule', _)} = 1.
  
{assign(BodyAtom, true, (last_support, Rule, Atom))} :-
  last_support(Rule, Atom);
  pos_body(Rule, BodyAtom).
{assign(BodyAtom, false, (last_support, Rule, Atom))} :-
  last_support(Rule, Atom);
  neg_body(Rule, BodyAtom).

constraint(Rule) :-
  rule(Rule), head_bounds(Rule, LowerBound, UpperBound);
  #count{Atom : head(Rule, Atom), assign(Atom, true, _)} > UpperBound.
constraint(Rule) :-
  rule(Rule), head_bounds(Rule, LowerBound, UpperBound);
  #sum{1, Atom : head(Rule, Atom); -1, Atom : head(Rule, Atom), assign(Atom, false, _)} < LowerBound.

{assign(Atom, false, (constraint, Rule))} :-
  constraint(Rule), pos_body(Rule, Atom);
  assign(Atom', true, _) : pos_body(Rule, Atom'), Atom' != Atom;
  assign(Atom', false, _) : neg_body(Rule,Atom').
{assign(Atom, true, (constraint, Rule))} :-
  constraint(Rule), neg_body(Rule, Atom);
  assign(Atom', true, _) : pos_body(Rule, Atom');
  assign(Atom', false, _) : neg_body(Rule,Atom'), Atom' != Atom.
  
#show.
#show assign/3.
#show false_body/2.