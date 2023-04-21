"""
Test cases for main application functionality.
"""
from unittest import TestCase

from dumbo_asp.primitives import SymbolicProgram, Model, GroundAtom

from ucorexplain import explain


class TestMain(TestCase):
    """
    Test cases for explain
    """

    @staticmethod
    def assert_explain_suffix(program: SymbolicProgram, suffix: str):
        assert str(program).strip().endswith('\n' + suffix.strip())

    def test_subprogram_free_choice(self):
        program = SymbolicProgram.parse("""
        {c}.
        """)
        query_atom = GroundAtom.parse("c")
        answer_set = Model.of_program("c.")
        result = explain(
            program=program,
            answer_set=answer_set,
            query_atom=query_atom,
            priority_list=tuple(GroundAtom.parse(atom) for atom in [
                "c",
            ]),
        )
        self.assertIsNone(result)

    def test_subprogram_free(self):
        program = SymbolicProgram.parse("""
        a.
        {c} :- a.
        b :- c.
        """)
        query_atom = GroundAtom.parse("c")
        answer_set = Model.of_program("a. b. c.")
        result = explain(
            program=program,
            answer_set=answer_set,
            query_atom=query_atom,
            priority_list=tuple(GroundAtom.parse(atom) for atom in [
                "a",
                "b",
                "c",
            ]),
        )
        self.assert_explain_suffix(result, "__mus__(priority_list,1).  %* b *%")

    def test_subprogram_selecting_choice(self):
        program = SymbolicProgram.parse("""
        1{a}.
        b:-a.
        b:-not a.
        """)
        query_atom = GroundAtom.parse("b")
        answer_set = Model.of_program("a. b.")
        result = explain(
            program=program,
            answer_set=answer_set,
            query_atom=query_atom,
            priority_list=tuple(GroundAtom.parse(atom) for atom in [
                "a",
                "b",
            ]),
        )
        self.assert_explain_suffix(result, """
__mus__(program,0).  %* 1{a}. *%
__mus__(program,1).  %* b:-a. *%
        """)

    def test_subprogram_simple(self):
        program = SymbolicProgram.parse("""
        a.
        {c}:-a.
        d:-c.
        b:-d.
        """)
        query_atom = GroundAtom.parse("b")
        answer_set = Model.of_program("a. b. c. d.")
        result = explain(
            program=program,
            answer_set=answer_set,
            query_atom=query_atom,
            priority_list=tuple(GroundAtom.parse(atom) for atom in [
                "a",
                "b",
                "c",
                "d",
            ]),
        )
        self.assert_explain_suffix(result, """
__mus__(program,2).  %* d:-c. *%
__mus__(program,3).  %* b:-d. *%
__mus__(priority_list,2).  %* c *%
        """)

    def test_subprogram_simple_d_first(self):
        program = SymbolicProgram.parse("""
        a.
        {c}:-a.
        d:-c.
        b:-d.
        """)
        query_atom = GroundAtom.parse("b")
        answer_set = Model.of_program("a. b. c. d.")
        result = explain(
            program=program,
            answer_set=answer_set,
            query_atom=query_atom,
            priority_list=tuple(GroundAtom.parse(atom) for atom in [
                "a",
                "b",
                "d",
                "c",
            ]),
        )
        self.assert_explain_suffix(result, """
__mus__(program,3).  %* b:-d. *%
__mus__(priority_list,2).  %* d *%
        """)

        # Would like to use rules before priority list right? YES