"""
UCOREXPLAIN
"""


from typing import Final, Optional, Union

import clingo
import typeguard
from dumbo_asp.primitives import SymbolicAtom, SymbolicRule, SymbolicProgram, Model, GroundAtom
from dumbo_utils.console import console
from rich.progress import Progress

AnswerSetElement = Union[GroundAtom, tuple[GroundAtom, bool]]
AnswerSet = tuple[AnswerSetElement, ...]


def unpack_answer_set_element(element: AnswerSetElement) -> tuple[GroundAtom, bool]:
    if type(element) != GroundAtom:
        return element
    return element, True


def move_up(answer_set: AnswerSet, *pattern: SymbolicAtom) -> AnswerSet:
    def key(element):
        atom, truth_value = unpack_answer_set_element(element)
        return 0 if SymbolicAtom.of_ground_atom(atom).match(*pattern) else 1

    return tuple(sorted(answer_set, key=key))


def answer_set_to_constraints(
        answer_set: AnswerSet,
        query_atom: GroundAtom,
        mus_predicate: str
) -> list[SymbolicRule]:
    """
    Produces the sequence of selecting constraints.
    """
    constraints = []
    for index, element in enumerate(answer_set):
        atom, truth_value = unpack_answer_set_element(element)
        if atom == query_atom:
            constraints.append(f":- {'' if truth_value else 'not'} {atom}.  % Query")
        else:
            constraints.append(
                f":- {'not' if truth_value else ''} {atom}, {mus_predicate}(answer_set,{index}).  % Answer set"
            )

    return [SymbolicRule.parse(constraint) for constraint in constraints]


def build_extended_program_and_selectors(
        program: SymbolicProgram,
        answer_set: AnswerSet,
        query_atom: GroundAtom,
        mus_predicate: str
) -> tuple[SymbolicProgram, list[GroundAtom]]:
    rules = [rule.with_extended_body(SymbolicAtom.parse(f"{mus_predicate}(program,{index})"))
             for index, rule in enumerate(program)]

    constraints = answer_set_to_constraints(answer_set, query_atom, mus_predicate)
    extended_program = SymbolicProgram.of(rules, constraints, SymbolicRule.parse(
        "{" +
        f"{mus_predicate}(program,0..{len(rules) - 1}); "
        f"{mus_predicate}(answer_set,0..{len(constraints) - 1})" +
        "}."
    ))
    selectors = [GroundAtom.parse(f"{mus_predicate}(program,{index})") for index in range(len(rules))] + \
        [GroundAtom.parse(f"{mus_predicate}(answer_set,{index})") for index in range(len(constraints))]
    return extended_program, selectors


def build_control_and_maps(
        extended_program: SymbolicProgram,
        mus_predicate: str,
):
    control = clingo.Control()
    control.add(str(extended_program))
    control.ground([("base", [])])
    selector_to_literal = {}
    literal_to_selector = {}
    for atom in control.symbolic_atoms.by_signature(mus_predicate, 2):
        selector = GroundAtom.parse(str(atom.symbol))
        selector_to_literal[selector] = atom.literal
        literal_to_selector[atom.literal] = selector

    return control, selector_to_literal, literal_to_selector


def check(
        control: clingo.Control,
        with_selectors: list[GroundAtom],
        selector_to_literal: dict[GroundAtom, int],
        literal_to_selector: dict[int, GroundAtom],
) -> Optional[list[GroundAtom]]:
    def on_core(core):
        on_core.res = core
    on_core.res = []

    control.solve(assumptions=[selector_to_literal[selector] for selector in with_selectors] + [-1],
                  on_core=on_core)

    if on_core.res and on_core.res[-1] != -1:
        return [literal_to_selector[literal] for literal in on_core.res]


@typeguard.typechecked
def explain(
    program: SymbolicProgram,
    answer_set: AnswerSet,
    query_atom: GroundAtom,
) -> Optional[SymbolicProgram]:
    mus_predicate: Final = f"__mus__"

    extended_program, selectors = build_extended_program_and_selectors(
        program, answer_set, query_atom, mus_predicate
    )
    console.print("[bold blue]-----------------[/bold blue]")
    console.print(f"[bold blue]Extended program:[/bold blue]")
    for line in extended_program:
        console.print(f"{line}")
    console.print("[bold blue]-----------------[/bold blue]")

    control, selector_to_literal, literal_to_selector = build_control_and_maps(extended_program, mus_predicate)

    console.log(f"Initial check with {len(selectors) - 1} selectors...")  # selector of the query is always true
    result = check(
        control=control,
        with_selectors=selectors,
        literal_to_selector=literal_to_selector,
        selector_to_literal=selector_to_literal
    )
    if result is None:
        console.log(f"  It's a free choice. Stop!")
        return
    console.log(f"  Shrink to {len(result)} selectors!")
    selectors = result

    with Progress(console=console, transient=True) as progress:
        task = progress.add_task("Searching MUS...", total=len(selectors))
        required_selectors = 0

        while required_selectors < len(selectors):
            console.log(f"Flag {selectors[-1]} as required!")
            required_selectors += 1
            selectors.insert(0, selectors.pop())  # last selector is required... move it ahead
            console.log(f"Check with {len(selectors)} selectors...")
            result = check(
                control=control,
                with_selectors=selectors,
                literal_to_selector=literal_to_selector,
                selector_to_literal=selector_to_literal
            )
            assert result is not None
            console.log(f"  Shrink to {len(result)} selectors!")
            progress.update(task, advance=len(selectors) - len(result))
            selectors = result

    console.log(f"Terminate with {len(selectors)} selectors!")

    def selector_to_rule(selector):
        return program[selector.arguments[1].number] if selector.arguments[0].name == 'program' else \
            answer_set[selector.arguments[1].number]

    selectors_program = '\n'.join(f"{selector}.  %* {selector_to_rule(selector)} *%" for selector in selectors)
    return SymbolicProgram.parse(f"{extended_program}\n\n{selectors_program}")


@typeguard.typechecked
def print_output(
        query_atom: GroundAtom,
        result: SymbolicProgram,
):
    console.print("[bold red]Explanation:[/bold red]")
    if result is not None:
        console.print(f"% {query_atom} is explained by")
        console.print(f"{result}")
    else:
        console.print(f"% {query_atom} is a free choice")


# def print_program(sudoku_instance: str):
#     instance = [line.strip() for line in sudoku_instance.strip().split('\n')]
#     given = []
#     for row, row_line in enumerate(instance, start=1):
#         for col, value in enumerate(row_line, start=1):
#             if value != '.':
#                 given.append(f"given(({row}, {col}), {value}).")

#     sub_blocks = []
#     for row in range(3):
#         for col in range(3):
#             sub_blocks.append(
#                 f"block((sub, {row}, {col}), (Row, Col)) :- Row = {row * 3 + 1}..{(row + 1) * 3}; Col = {col * 3 + 1}..{(col + 1) * 3}.")

#     program = SymbolicProgram.parse("""
#     {assign((Row, Col), Value) : Value = 1..9} = 1 :- Row = 1..9; Col = 1..9.
#     :- block(Block, Cell); block(Block, Cell'), Cell != Cell'; assign(Cell, Value), assign(Cell', Value).
#     :- given(Cell, Value), not assign(Cell, Value).
#     """ + '\n'.join(f"block((row, {row + 1}), ({row + 1}, Col)) :- Col = 1..9." for row in range(9)) + """
#     """ + '\n'.join(f"block((col, {col + 1}), (Row, {col + 1})) :- Row = 1..9." for col in range(9)) + """
#     """ + '\n'.join(sub_blocks) + """
#     block((sub, (Row-1) / 3, (Col-1) / 3), (Row, Col)) :- Row = 1..9; Col = 1..9.
#         """ + '\n'.join(given))
#     print(program)