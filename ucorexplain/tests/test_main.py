"""
Test cases for main application functionality.
"""
import logging
from io import StringIO
from unittest import TestCase

from ucorexplain.utils.logger import setup_logger
from ucorexplain.utils.parser import get_parser

from .. import explain, print_output
from dumbo_asp.primitives import SymbolicAtom, SymbolicRule, SymbolicProgram, Model, GroundAtom

class TestMain(TestCase):
    """
    Test cases for explain
    """

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
        {c}:-a.
        b:-c.
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
        result_prg = [str(rule) for rule in result]
        self.assertEqual(result_prg[0],'b')


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
        result_prg = [str(rule) for rule in result]
        self.assertIn('1{a}.',result_prg)


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
        result_prg = [str(rule) for rule in result]
        self.assertEqual(result_prg[-1],'c')

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
        result_prg = [str(rule) for rule in result]
        self.assertEqual(result_prg[-1],'d')

        # Would like to use rules before priority list right?