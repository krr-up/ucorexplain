head_bounds(Rule, LowerBound, UpperBound) :-
  rule(Rule), choice(Rule, LowerBound, UpperBound).
head_bounds(Rule, 1, Size) :- 
  rule(Rule), not choice(Rule,_,_); 
  Size = #count{HeadAtom : head(Rule, HeadAtom)}.

atom(Atom) :- head(Rule, Atom).
atom(Atom) :- pos_body(Rule, Atom).
atom(Atom) :- neg_body(Rule, Atom). 