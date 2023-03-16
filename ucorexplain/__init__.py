"""
UCOREXPLAIN
"""


from typing import Final, Optional

import clingo
import typeguard
from dumbo_utils.console import console
from rich.progress import Progress

from dumbo_asp.primitives import SymbolicAtom, SymbolicRule, SymbolicProgram, Model, GroundAtom


def priority_list_to_constraints(
        answer_set: Model,
        query_atom: GroundAtom,
        priority_list: tuple[GroundAtom, ...],
        mus_predicate: str
) -> list[SymbolicRule]:
    """
    Produces the sequence of selecting constraints.
    """
    constraints = []
    for index, atom in enumerate(priority_list):
        if atom == query_atom:
            if atom in answer_set:
                constraints.append(f":- %* explain truth of {atom} *%  {atom}.")
            else:
                constraints.append(f":- %* explain falsity of {atom} *%  not {atom}.")
        else:
            if atom in answer_set:
                constraints.append(f":- %* enforce truth of   {atom} (it belongs to the answer set)        *%  "
                                   f"not  {atom}, {mus_predicate}(priority_list,{index}).")
            else:
                constraints.append(f":- %* enforce falsity of {atom} (it doesn't belong to the answer set) *%  "
                                   f"     {atom}, {mus_predicate}(priority_list,{index}).")

    return [SymbolicRule.parse(constraint) for constraint in constraints]


def build_extended_program_and_selectors(
        program: SymbolicProgram,
        answer_set: Model,
        query_atom: GroundAtom,
        priority_list: tuple[GroundAtom, ...],
        mus_predicate: str
) -> tuple[SymbolicProgram, list[GroundAtom]]:
    rules = [rule.with_extended_body(SymbolicAtom.parse(f"{mus_predicate}(program,{index})"))
             for index, rule in enumerate(program)]
    constraints = priority_list_to_constraints(answer_set, query_atom, priority_list, mus_predicate)
    return SymbolicProgram.of(rules, constraints, SymbolicRule.parse(
        "{" +
        f"{mus_predicate}(program,0..{len(rules) - 1}); "
        f"{mus_predicate}(priority_list,0..{len(constraints) - 1})" +
        "}."
    )), [GroundAtom.parse(f"{mus_predicate}(program,{index})") for index in range(len(rules))] + \
        [GroundAtom.parse(f"{mus_predicate}(priority_list,{index})") for index in range(len(constraints))]


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
        return with_selectors
        # can we drop to the core of clingo without breaking the priority?
        # return [literal_to_selector[literal] for literal in on_core.res]


@typeguard.typechecked
def explain(
    program: SymbolicProgram,
    answer_set: Model,
    query_atom: GroundAtom,
    priority_list: tuple[GroundAtom, ...],
):
    mus_predicate: Final = f"__mus__"

    extended_program, selectors = build_extended_program_and_selectors(
        program, answer_set, query_atom, priority_list, mus_predicate
    )

    control, selector_to_literal, literal_to_selector = build_control_and_maps(extended_program, mus_predicate)

    console.log(f"Initial check with {len(selectors)} selectors...")
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
            console.log(f"Check with {len(selectors) - 1} selectors "
                        f"(try to remove {len(selectors) - required_selectors - 1}) ...")
            result = check(
                control=control,
                with_selectors=[selector for index, selector in enumerate(selectors)
                                if index != len(selectors) - required_selectors - 1],
                literal_to_selector=literal_to_selector,
                selector_to_literal=selector_to_literal
            )
            if result is None:
                console.log(f"  Flag {selectors[-1 - required_selectors]} as required!")
                progress.update(task, advance=1)
                required_selectors += 1
            else:
                console.log(f"  Shrink to {len(result)} selectors!")
                progress.update(task, advance=len(selectors) - len(result))
                selectors = result

    console.log(f"Terminate with {len(selectors)} selectors!")
    return [
        program[selector.arguments[1].number] if selector.arguments[0].name == 'program' else
        priority_list[selector.arguments[1].number]
        for selector in selectors
    ]


@typeguard.typechecked
def print_output(
        query_atom: GroundAtom,
        result: list[SymbolicRule],
):
    console.print("[bold red]Explanation:[/bold red]")
    if result is not None:
        console.print(f"{query_atom} is explained by")
        for line in result:
            console.print(f"  {line}")
    else:
        console.print(f"{query_atom} is a free choice")


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