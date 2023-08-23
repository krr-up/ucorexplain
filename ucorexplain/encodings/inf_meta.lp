% conjunction(B) :- literal_tuple(B), 
%     hold(L) : literal_tuple(B, L), L > 0; 
%     not hold(L) : literal_tuple(B, -L), L > 0. 
% 
% body(normal(B)) :- rule(_,normal(B)), conjunction(B). 
% body(sum(B,G)) :- rule(_,sum(B,G)), 
%     #sum { W,L : hold(L), weighted_literal_tuple(B, L,W), L > 0 ; 
%            W,L : not hold(L), weighted_literal_tuple(B, -L,W), L > 0 } >= G. 
% 
% hold(A) : atom_tuple(H,A) :- rule(disjunction(H),B), body(B). 
% { hold(A) : atom_tuple(H,A) } :- rule(choice(H),B), body(B). 
% 
% :- __core__(C), output(C,B), not conjunction(B).

order(1..i).  % inference order

_t(X,0) :- __core__(C), output(C,LT), literal_tuple(LT), literal_tuple(LT,X).

rule_dom(disjunction(D),normal(R)) :-  __core__(C), output(C,LT), literal_tuple(LT), literal_tuple(LT,X),
    literal_tuple(R,X), rule(disjunction(D),normal(R)).


%%%%%%%%%%%%%%%%%%%%%%%%%
%                       %
% Avoid inconsistencies %
%                       %
%%%%%%%%%%%%%%%%%%%%%%%%%

_f(U,I,avoid_inconsistency) :- rule(disjunction(D),normal(R)), 
    _f(A,I-1): atom_tuple(D,A);  % head is false
    literal_tuple(R,U), U>0,  % infered literal from positive body
    not _f(U,I-1), not _t(U,I-1), order(I),
    _t(B,I-1): literal_tuple(R,B), B!=U, B>0;  % other positive body literals are true
    _f(-B,I-1): literal_tuple(R,B), B!=U, B<0.  % other negative body literal are false

_t(-U,I,avoid_inconsistency) :- rule(disjunction(D),normal(R)), 
    _f(A,I-1): atom_tuple(D,A);  % head is false
    literal_tuple(R,U), U<0,  % infered literal from negative body
    not _f(-U,I-1), not _t(-U,I-1), order(I),
    _t(B,I-1): literal_tuple(R,B), B!=U, B>0;  % other positive body literals are true
    _f(-B,I-1): literal_tuple(R,B), B!=U, B<0.  % other negative body literals are false


%%%%%%%%%%%%%%%%%%%%%%%%%
%                       %
%       Support         %
%                       %
%%%%%%%%%%%%%%%%%%%%%%%%%

_t(A,I,support) :- rule(disjunction(D),normal(R)), 
    atom_tuple(D,A), order(I),
    not _f(A,I-1), not _t(A,I-1),   % head is undecided
    _t(B,I-1): literal_tuple(R,B), B>0;  % positive body is satisfied
    _f(-B,I-1): literal_tuple(R,B), B<0. % negative body is satisfied


%%%%%%%%%%%%%%%%%%%%%%%%%
%                       %
%   Backward Support    %
%                       %
%%%%%%%%%%%%%%%%%%%%%%%%%

_false(conj(R),I) :- literal_tuple(R), literal_tuple(R,B), _f(B,I), B>0.
_false(conj(R),I) :- literal_tuple(R), literal_tuple(R,B), _t(-B,I), B<0.
     
_must_be_true(conj(R),I) :- rule(disjunction(D),normal(R)), not _false(conj(R),I),
    atom_tuple(D,A), _t(A,I),  % head is true (!! only for normal rule heads)
    #count{1,D',R': rule(disjunction(D'),normal(R')), atom_tuple(D',A), not _false(conj(R'),I);
           1,D',R': rule(choice(D'),normal(R')), atom_tuple(D',A), not _false(conj(R'),I)} = 1.

_t(B,I,backward_support) :- _must_be_true(conj(R),I-1), not _t(B,I-1), literal_tuple(R,B), B>0, order(I).
_f(-B,I,backward_support) :- _must_be_true(conj(R),I-1), not _f(-B,I-1), literal_tuple(R,B), B<0, order(I).


%%%%%%%%%%%%%%%%%%%%%%%%%
%                       %
%    Lack of Support    %
%                       %
%%%%%%%%%%%%%%%%%%%%%%%%%

_f(A,I,lack_of_support) :- atom_tuple(_,A), not _f(A,I-1), order(I),
    _false(conj(R),I-1): atom_tuple(D,A), rule(disjunction(D),normal(R));  % all supporting bodies are false
    _false(conj(R),I-1): atom_tuple(D,A), rule(choice(D),normal(R)).  % all supporting bodies are false
   


_f(U,I) :- _f(U,I,_).
_t(U,I) :- _t(U,I,_).

_f(U,I) :- _f(U,I-1), order(I).
_t(U,I) :- _t(U,I-1), order(I).

% Query must be satisfied
:- output(__mus__,L), literal_tuple(L,A), not _t(A,i).

true(A,I,R) :- _t(A,I,R), atom_tuple(_,A), not literal_tuple(_,A).
false(A,I,R) :- _f(A,I,R), atom_tuple(_,A), not literal_tuple(_,A).
true(O,I,R) :- _t(A,I,R), literal_tuple(L,A), output(O,L).
false(O,I,R) :- _f(A,I,R), literal_tuple(L,A), output(O,L).

#show true/3.
#show false/3.
