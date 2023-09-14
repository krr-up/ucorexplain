"""
Test cases for main application functionality.
"""
from typing import Optional
from unittest import TestCase

import clingo
import pytest
from dumbo_asp.primitives import SymbolicProgram, Model, GroundAtom, SymbolicAtom, Predicate, SymbolicRule
from dumbo_asp.queries import open_graph_in_xasp_navigator

from ucorexplain import (
    answer_set_element_to_string,
    get_answer_set,
    get_mus_program_and_selectors,
)


class TestMain(TestCase):
    """
    Test cases for explain
    """

    @staticmethod
    def assert_selectors(
        selectors: list,
        selectors_found: list,
    ):
        if selectors is None:
            assert len(selectors_found) == 0
            return
        selectors_found_list = [
            answer_set_element_to_string(s) for s in selectors_found
        ]
        for s in selectors:
            assert s.split(".")[0] in selectors_found_list

    @staticmethod
    def check_query(
        program: str, query_atom: str, answer_set: str, selectors: Optional[str]
    ):
        """
        Check if the query against the program and answer set produces the selectors in answer.

        :param program: The input program, as a string
        :param query_atom: One or more atoms, as a space-separated list of strings
        :param answer_set: Zero or more literals, as a space-separated list of strings.
            False literals starts with ~, and atoms in the Herbrand base of the program
            not occurring in answer_set are considered false.
        :param selectors: The selectors that are expected to be responsible for the derivation of the query, or
            None if the query is expected to be a free choice.
        :returns: Nothing, but raises an error if the actual outcome doesn't match the expected outcome
        """

        program = SymbolicProgram.parse(program)
        # the_answer_set = []
        # if answer_set:
        #     for atom in answer_set.split(' '):
        #         the_answer_set.append(
        #             (GroundAtom.parse(atom[1:]), False) if atom.startswith('~') else (GroundAtom.parse(atom), True)
        #         )
        # # ALL ATOMS THAT ARE NOT MENTIONED IN THE ANSWER SET ARE FALSE.
        # # IF WE WANT THE USER TO SPECIFY ALL ATOMS THAT ARE TRUE, WE CAN MOVE THIS CODE IN THE explain() FUNCTION.
        # atoms_in_the_answer_set = set(element[0] for element in the_answer_set)
        # herbrand_base = the_program.to_zero_simplification_version(
        #     extra_atoms=atoms_in_the_answer_set,
        #     compact=True
        # ).herbrand_base_without_false_predicate
        # for atom in herbrand_base:
        #     if atom not in atoms_in_the_answer_set:
        #         the_answer_set.append((atom, False))

        answer_set = get_answer_set(answer_set)
        query = tuple(GroundAtom.parse(atom) for atom in query_atom.split(" "))

        mus_prg, selectors_found = get_mus_program_and_selectors(
            program=program, answer_set=tuple(answer_set), query_atom=query
        )

        TestMain.assert_selectors(
            selectors=selectors,
            selectors_found=selectors_found,
        )

    def test_subprogram_free_choice(self):
        self.check_query(
            program="""
            {c}.
            """,
            query_atom="c",
            answer_set="c",
            selectors=None,
        )

    def test_choice_rule_and_constraint_inference_by_constraint(self):
        """
        The choice rule alone doesn't cause the inference of atom c.
        It is actually the constraint that infers c.
        """
        self.check_query(
            program="""
            {c}.
            :- not c.
            """,
            query_atom="c",
            answer_set="c",
            selectors=[
                "__mus__(program,1).  %* :- not c. *%",
            ],
        )

    def test_choice__multiple_queries(self):
        """
        Multiple queries
        """
        self.check_query(
            program="""
            {a;b;c}.
            :- not a, not b, not c.
            :- not a, b.
            :- a, not b.
            :- a, b.
            """,
            query_atom="c a",
            answer_set="c",
            selectors=[
                "__mus__(program,1).  %* :- not a, not b, not c. *%",
                "__mus__(program,3).  %* :- a, not b. *%",
                "__mus__(answer_set,0).  %* not b *%",
            ],
        )

    def test_choice__multiple_queries_free_choice(self):
        """
        Can't be entailed using only propagation, one of them must be taken from the answer set
        But since all of them are part of the query they are removed, thus "Free Choice"
        """
        self.check_query(
            program="""
            {a;b;c}.
            :- not a, not b, c.
            :- not a, b.
            :- a, not b.
            :- a, b.
            """,
            query_atom="c a b",
            answer_set="c ~a ~b",
            selectors=None
        )

    def test_well_founded_inference_1(self):
        """
        Well-founded computation is disabled, so falsity of a is established after assuming the falsity of b.
        """
        self.check_query(
            program="""
            a :- b.
            b :- a.
            """,
            query_atom="a",
            answer_set="~a ~b",
            selectors=[
            "__mus__(answer_set,0).  %* not b *%"
            ]
        )

    def test_well_founded_inference_2(self):
        """
        Falsity of a is established after assuming falsity of c and b.
        """
        self.check_query(
            program="""
            {c}.
            a :- c.
            a :- b.
            b :- a.
            """,
            query_atom="a",
            answer_set="~c ~b ~a",
            selectors=[
            "__mus__(answer_set,0).  %* not c *%",
            "__mus__(answer_set,1).  %* not b *%",
            ]
        )

    def test_well_founded_inference_3(self):
        """
        Changing the priority of atoms may give a different explanation.
        After guessing the falsity of b, atom a is inferred false because of rule  b :- a.
        """
        self.check_query(
            program="""
            {c}.
            a :- c.
            a :- b.
            b :- a.
            """,
            query_atom="a",
            answer_set="~a ~b ~c",
            selectors=[
                "__mus__(program,3).  %* b :- a. *%",
                "__mus__(answer_set,0).  %* not b *%",
            ],
        )

    def test_simple_loop_with_choice_rule_1(self):
        """
        Truth of atom a is inferred after "guessing" b true
        because b has only one potentially supporting rule whose body containing a (and also a selector literal).
        """
        self.check_query(
            program="""
            {a}.
            a :- b.
            b :- a.
            """,
            query_atom="a",
            answer_set="a b",
            selectors=["__mus__(answer_set,0).  %* b *%"],
        )

    def test_simple_loop_with_choice_rule_2(self):
        """
        Truth of b is inferred after "guessing" a true by the support given by rule  b :- a.
        """
        self.check_query(
            program="""
            {a}.
            a :- b.
            b :- a.
            """,
            query_atom="b",
            answer_set="a b",
            selectors=[
                "__mus__(program,2).  %* b :- a. *%",
                "__mus__(answer_set,0).  %* a *%",
            ],
        )

    def test_simple_loop_with_choice_rule_3(self):
        """
        Truth of "a and b" is a free choice, as there is another answer set in which they are false.
        """
        self.check_query(
            program="""
            {a}.
            a :- b.
            b :- a.
            """,
            query_atom="a b",
            answer_set="a b",
            selectors=None,
        )

    def test_inference_by_support(self):
        self.check_query(
            program="""
            a.
            b :- a.
            """,
            query_atom="b",
            answer_set="a b",
            selectors=[
                "__mus__(program,0).  %* a. *%",
                "__mus__(program,1).  %* b :- a. *%",
            ],
        )

    def test_inference_by_lack_of_support_1(self):
        """
        After guessing a false, b has no support and is inferred false.
        """
        self.check_query(
            program="""
            {a}.
            b :- a.
            """,
            query_atom="b",
            answer_set="",
            selectors=["__mus__(answer_set,0).  %* not a *%"],
        )

    def test_inference_by_lack_of_support_2(self):
        """
        After guessing a false, b has no support and is inferred false.
        """
        self.check_query(
            program="""
            {a; a'}.
            b :- a.
            b :- a'.
            """,
            query_atom="b",
            answer_set="",
            selectors=[
                "__mus__(answer_set,0).  %* not a *%",
                "__mus__(answer_set,1).  %* not a' *%",
            ],
        )

    def test_subprogram_free(self):
        self.check_query(
            program="""
            a.
            {c} :- a.
            b :- c.
            """,
            query_atom="c",
            answer_set="a b c",
            selectors=["__mus__(answer_set,1).  %* b *%"],
        )

    def test_subprogram_selecting_choice(self):
        self.check_query(
            program="""
            1{a}.
            b:-a.
            b:-not a.
            """,
            query_atom="b",
            answer_set="a b",
            selectors=[
                "__mus__(program,0).  %* 1{a}. *%",
                "__mus__(program,1).  %* b:-a. *%",
            ],
        )

    def test_subprogram_simple(self):
        self.check_query(
            program="""
            a.
            {c}:-a.
            d:-c.
            b:-d.
            """,
            query_atom="b",
            answer_set="a b c d",
            selectors=[
                "__mus__(program,2).  %* d:-c. *%",
                "__mus__(program,3).  %* b:-d. *%",
                "__mus__(answer_set,1).  %* c *%",
            ],
        )

    def test_subprogram_simple_d_first(self):
        self.check_query(
            program="""
            a.
            {c}:-a.
            d:-c.
            b:-d.
            """,
            query_atom="b",
            answer_set="a b c d",
            selectors=[
                "__mus__(program,3).  %* b:-d. *%",
                "__mus__(answer_set,1).  %* d *%",
            ],
        )

    def test_multiple_atoms_can_be_free_choices(self):
        self.check_query(
            program="""
            {a}.
            b :- a.
            """,
            query_atom="a b",
            answer_set="a b",
            selectors=None,
        )

    def test_not_removed_in_ground(self):
        self.check_query(
            program="""
            a.
            b:- not a.
            """,
            query_atom="b",
            answer_set="a",
            selectors=["__mus__(program,0)"],
        )
        assert result is None

        assert result is None

    #@pytest.mark.skip(reason="Structure the code in this 'test' so that we can call it in a convenient way")
    def test_foo(self):
        program = SymbolicProgram.parse("""
%*
3 . . .
. . . 2
1 . . .
. . . 1
*%
given((1,1), 3).
given((2,4), 2).
given((3,1), 1).
given((4,4), 1).
        
{assign((Row, Col), Value) : Value = 1..4} = 1 :- Row = 1..4; Col = 1..4.
% assign((Row, Col), Value) : Value = 1..4 :- Row = 1..4; Col = 1..4.
:- given(Cell, Value), not assign(Cell, Value).

:- block(Block, Cell); block(Block, Cell'), Cell != Cell'; assign(Cell, Value), assign(Cell', Value).
:- block(Block, Cell'); Value = 1..4; not assign(Cell, Value) : block(Block, Cell).

block((row, Row), (Row, Col)) :- Row = 1..4, Col = 1..4.
block((col, Col), (Row, Col)) :- Row = 1..4, Col = 1..4.
block((sub, Row', Col'), (Row, Col)) :- Row = 1..4; Col = 1..4; Row' = (Row-1) / 2; Col' = (Col-1) / 2.
        """)

        model = Model.of_program(program).filter(when=lambda atom: atom.predicate_name == 'assign')
        #print(model.as_facts)
        #assert False
        query = GroundAtom.parse("assign((1,2),2)")

        # COMPUTE THE HERBRAND BASE OF THE ZERO-SIMPLIFICATION VERSION (TO BE USED TO EXPAND VARIABLES OF THE INPUT PROGRAM)
        herbrand_base = program.to_zero_simplification_version(
            # extra_atoms=Model.of_program("any(extra,atom). that(make,sense). to. add."),
            compact=True
        ).herbrand_base_without_false_predicate

        # LET USERS EXPAND THE VARIABLES THEY LIKE AND REORDER THE PROGRAM AS THEY WISH
        program = program.expand_global_safe_variables(rule=program[-5], variables=["Block"], herbrand_base=herbrand_base)
        program = program.move_up(SymbolicAtom.parse("block(Block, Cell)"))

        # COMPUTE THE SELECTORS, THEN EXPAND ALL VARIABLES AND SERIALIZE THE GROUND PROGRAM
        mus_program = explain(
            program=program,
            answer_set=tuple(atom for atom in model),
            query_atom=query
        )
        #print(mus_program)
        #assert False
        mus_program = mus_program.expand_global_and_local_variables()
        #with open("/tmp/foo", "w") as f:
        #    f.write(str(mus_program))
        #assert False
        serialization = Model.of_program(SymbolicProgram.parse(Model.of_atoms(mus_program.serialize(
            base64_encode=False,
        )).as_facts + """
head_bounds(Rule, LowerBound, UpperBound) :-
  rule(Rule), choice(Rule, LowerBound, UpperBound).
head_bounds(Rule, 1, Size) :- 
  rule(Rule), not choice(Rule,_,_); 
  Size = #count{HeadAtom : head(Rule, HeadAtom)}.

atom(Atom) :- head(Rule, Atom).
atom(Atom) :- pos_body(Rule, Atom).
atom(Atom) :- neg_body(Rule, Atom).        
        """ + f'query("{query}").'))
        # print("\n\n\n*** SERIALIZATION ***\n\n")
        # print(serialization.as_facts)
        # # print(mus_program.serialize(
        # #     base64_encode=False,
        # # ).as_facts)
        # assert False

        # META-ENCODING FOR THE PROPAGATION
        derivation_sequence = []
        propagate_program = serialization.as_facts + """
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
        """
        #with open("/tmp/foo", "w") as f:
        #    f.write(str(propagate_program))
        #assert False
        control = clingo.Control()
        control.add(str(propagate_program))
        control.ground([("base", [])])
        def m(atoms):
            for atom in atoms.symbols(shown=True):
                at = GroundAtom.parse(str(atom))
                derivation_sequence.append(f"{at.predicate_name}({','.join(str(arg) for arg in at.arguments)},{len(derivation_sequence) + 1})")
        control.solve(on_model=m)
        derivation_sequence = Model.of_atoms(derivation_sequence)
        # WARNING! Here I'm assuming that atoms are ordered according to the derivation in the solver. If it is not, we need a propagator or something different

        #print("\n\n\n***\n\n")
        #print(derivation_sequence.as_facts)
        #assert False

        # BUILD GRAPH WITH ANOTHER META-ENCODING
        # I'M HIDING THE __mus__ ATOMS, BUT WE CAN OPT FOR SOMETHING DIFFERENT
        graph_program = SymbolicProgram.parse(serialization.as_facts + derivation_sequence.as_facts + """
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
        """)
        #with open("/tmp/foo", "w") as f:
        #   f.write(str(graph_program))
        #assert False

        # SHOW THE GRAPH IN THE NAVIGATOR (IT NEEDS SOME WORK TO GIVE MORE FREEDOM ON COLORS AND LABELS)
        open_graph_in_xasp_navigator(
            Model.of_program(graph_program)
            .filter(when=lambda atom: atom.predicate_name in ["node", "link'"])
            .rename(Predicate.parse("link'"), Predicate.parse("link"))
        )

        assert False


