{a} :- __mus__(program,0).
a :- b; __mus__(program,1).
b :- a; __mus__(program,2).
:- not a, __mus__(answer_set,0)  %* Answer set *% .
__mus__ :- b.
{__mus__(program,0..2); __mus__(answer_set,0..0)}.
