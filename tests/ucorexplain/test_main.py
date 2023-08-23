"""
Test cases for main application functionality.
"""
from typing import Optional
from unittest import TestCase

from dumbo_asp.primitives import SymbolicProgram, Model, GroundAtom

from ucorexplain import get_mus_program, answer_set_element_to_string


class TestMain(TestCase):
    """
    Test cases for explain
    """

    @staticmethod
    def assert_mus_prg(program: SymbolicProgram, selectors: list, selectors_found: list,):
        selectors_found_list = [answer_set_element_to_string(s) for s in selectors_found]
        for s in selectors:
            assert s.split(".")[0] in selectors_found_list

    @staticmethod
    def check_query(program: str, query_atom: str, answer_set: str, selectors: Optional[str]):
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
        the_program = SymbolicProgram.parse(program)

        the_answer_set = []
        if answer_set:
            for atom in answer_set.split(' '):
                the_answer_set.append(
                    (GroundAtom.parse(atom[1:]), False) if atom.startswith('~') else (GroundAtom.parse(atom), True)
                )
        # ALL ATOMS THAT ARE NOT MENTIONED IN THE ANSWER SET ARE FALSE.
        # IF WE WANT THE USER TO SPECIFY ALL ATOMS THAT ARE TRUE, WE CAN MOVE THIS CODE IN THE get_mus_program() FUNCTION.
        atoms_in_the_answer_set = set(element[0] for element in the_answer_set)
        for atom in the_program.herbrand_base:
            if atom not in atoms_in_the_answer_set:
                the_answer_set.append((atom, False))

        mus_prg, selectors_found = get_mus_program(
            program=the_program,
            answer_set=tuple(the_answer_set),
            query_atom=tuple(
                GroundAtom.parse(atom) for atom in query_atom.split(' ')
            ),
        )
        if mus_prg is None or selectors is None:
            assert mus_prg == selectors
        else:
            TestMain.assert_mus_prg(
                program=mus_prg,
                selectors=selectors,
                selectors_found =selectors_found,
            )

    def test_subprogram_free_choice(self):
        program = SymbolicProgram.parse("""
        {c}.
        """)
        query_atom = GroundAtom.parse("c")
        answer_set = tuple(Model.of_program("c."))
        result, selectors = get_mus_program(
            program=program,
            answer_set=answer_set,
            query_atom=query_atom,
        )
        self.assertIsNone(result)

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
            ]
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
            ]
        )

    def test_choice__multiple_queries_free_choice(self):
        """
        Can't be entailed using only propagation, one of them must be taken from the answer set
        But since all of them are part of the query they are removed, thus "Free Choice"
        """
        self.check_query(
            program="""
            {a;b;c}.
            :- not a, not b, not c.
            :- not a, b.
            :- a, not b.
            :- a, b.
            """,
            query_atom="c a b",
            answer_set="c",
            selectors=None
        )

    def test_well_founded_inference_1(self):
        """
        A simple unfounded loop. Falsity of atom a is explained with no selectors: atom a is false wrt. any subprogram.
        """
        self.check_query(
            program="""
            a :- b.
            b :- a.
            """,
            query_atom="a",
            answer_set="",
            selectors=[]
        )

    def test_well_founded_inference_2(self):
        """
        A simple unfounded loop after "guessing" c false: atom a is false wrt. any subprogram if atom c is false.
        """
        self.check_query(
            program="""
            {c}.
            a :- c.
            a :- b.
            b :- a.
            """,
            query_atom="a",
            answer_set="~c",
            selectors=["__mus__(answer_set,0).  %* not c *%"]
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
            ]
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
            selectors=[
                "__mus__(answer_set,0).  %* b *%"
            ]
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
                "__mus__(answer_set,0).  %* a *%"
            ]
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
            selectors=None
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
            "__mus__(program,1).  %* b :- a. *%"
            ]
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
            selectors=[
            "__mus__(answer_set,0).  %* not a *%"
            ]
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
            "__mus__(answer_set,1).  %* not a' *%"]
        )

    def test_subprogram_free(self):
        program = SymbolicProgram.parse("""
        a.
        {c} :- a.
        b :- c.
        """)
        query_atom = GroundAtom.parse("c")
        answer_set = tuple(Model.of_program("a. b. c."))
        result, selectors = get_mus_program(
            program=program,
            answer_set=answer_set,
            query_atom=query_atom,
        )
        self.assert_mus_prg(result, ["__mus__(answer_set,1).  %* b *%"], selectors)

    def test_subprogram_selecting_choice(self):
        program = SymbolicProgram.parse("""
        1{a}.
        b:-a.
        b:-not a.
        """)
        query_atom = GroundAtom.parse("b")
        answer_set = tuple(Model.of_program("a. b."))
        result, selectors = get_mus_program(
            program=program,
            answer_set=answer_set,
            query_atom=query_atom,
        )
        self.assert_mus_prg(result, [
        "__mus__(program,0).  %* 1{a}. *%",
        "__mus__(program,1).  %* b:-a. *%",
        ],selectors)

    def test_subprogram_simple(self):
        program = SymbolicProgram.parse("""
        a.
        {c}:-a.
        d:-c.
        b:-d.
        """)
        query_atom = GroundAtom.parse("b")
        answer_set = tuple(Model.of_program("a. b. c. d."))
        result, selectors = get_mus_program(
            program=program,
            answer_set=answer_set,
            query_atom=query_atom,
        )
        self.assert_mus_prg(result, [
        "__mus__(program,2).  %* d:-c. *%",
        "__mus__(program,3).  %* b:-d. *%",
        "__mus__(answer_set,1).  %* c *%",
        ],selectors)

    def test_subprogram_simple_d_first(self):
        program = SymbolicProgram.parse("""
        a.
        {c}:-a.
        d:-c.
        b:-d.
        """)
        query_atom = GroundAtom.parse("b")
        answer_set = tuple(GroundAtom.parse(atom) for atom in "a b d c".split())
        result, selectors = get_mus_program(
            program=program,
            answer_set=answer_set,
            query_atom=query_atom,
        )
        self.assert_mus_prg(result, [
            "__mus__(program,3).  %* b:-d. *%",
            "__mus__(answer_set,1).  %* d *%"],selectors)

    def test_multiple_atoms_can_be_free_choices(self):
        program = SymbolicProgram.parse("""
        {a}.
        b :- a.
        """)
        query_atom = tuple(GroundAtom.parse(atom) for atom in "a b".split())
        answer_set = tuple(GroundAtom.parse(atom) for atom in "a b".split())
        result, selectors = get_mus_program(
            program=program,
            answer_set=answer_set,
            query_atom=query_atom,
        )
        assert result is None
