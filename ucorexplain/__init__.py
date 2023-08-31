"""
UCOREXPLAIN
"""


from typing import Final, Optional, Union, Sequence

import clingo
import typeguard
from dumbo_asp.primitives import SymbolicAtom, SymbolicRule, SymbolicProgram, Model, GroundAtom
from dumbo_utils.console import console
from rich.progress import Progress

AnswerSetElement = Union[GroundAtom, tuple[GroundAtom, bool]]
AnswerSet = tuple[AnswerSetElement, ...]

MUS_PREDICATE: Final = f"__mus__"

def unpack_answer_set_element(element: AnswerSetElement) -> tuple[GroundAtom, bool]:
    if type(element) != GroundAtom:
        return element
    return element, True


def answer_set_element_to_string(element: AnswerSetElement) -> str:
    if type(element) == GroundAtom:
        element = (element, True)
    return f"{'' if element[1] else 'not '}{element[0]}"


def move_up(answer_set: AnswerSet, *pattern: SymbolicAtom) -> AnswerSet:
    def key(element):
        atom, truth_value = unpack_answer_set_element(element)
        return 0 if SymbolicAtom.of_ground_atom(atom).match(*pattern) else 1

    return tuple(sorted(answer_set, key=key))


def program_from_files(files) -> SymbolicProgram:
    prg_str = ""
    for f in files:
        with open(f) as f:
            prg_str+= "\n".join(f.readlines())

    return SymbolicProgram.parse(prg_str)


def answer_set_to_constraints(
        answer_set: AnswerSet,
        query_atom: GroundAtom | tuple[GroundAtom, ...],
        mus_predicate: str
) -> list[SymbolicRule]:
    """
    Produces the sequence of selecting constraints.
    """
    if type(query_atom) == GroundAtom:
        query_atom = (query_atom,)
    query_atoms = set(query_atom)
    query_literals = []
    constraints = []
    for element in answer_set:
        atom, truth_value = unpack_answer_set_element(element)
        if atom in query_atoms:
            if truth_value:
                query_literals.append(f" {answer_set_element_to_string(atom)}")
            else:
                query_literals.append(f" not {answer_set_element_to_string(atom)}")
            query_atoms.remove(atom)
            pass
        else:
            constraints.append(
                f":- not {answer_set_element_to_string(element)}, {mus_predicate}(answer_set,{len(constraints)})"
                f"  %* Answer set *% ."
            )
    for atom in query_atoms:
        # TODO Removed not
        query_literals.append(f" {answer_set_element_to_string(atom)}")

    return [SymbolicRule.parse(constraint) for constraint in constraints] + \
        [SymbolicRule.parse(f"{mus_predicate} :- {', '.join(query_literals)}.")]

def build_extended_program_and_possible_selectors(
        program: SymbolicProgram,
        answer_set: AnswerSet,
        query_atom: GroundAtom | tuple[GroundAtom, ...],
        mus_predicate: str
) -> tuple[SymbolicProgram, list[GroundAtom]]:
    rules = [rule.with_extended_body(SymbolicAtom.parse(f"{mus_predicate}(program,{index})"))
             for index, rule in enumerate(program)]

    constraints = answer_set_to_constraints(answer_set, query_atom, mus_predicate)
    extended_program = SymbolicProgram.of(rules, constraints, SymbolicRule.parse(
        "{" +
        f"{mus_predicate}(program,0..{len(rules) - 1})" +
        (f"; {mus_predicate}(answer_set,0..{len(constraints) - 2})" if len(constraints) > 1 else "") +
        "}."
    ))
    selectors = [GroundAtom.parse(f"{mus_predicate}(program,{index})") for index in range(len(rules))] + \
        [GroundAtom.parse(f"{mus_predicate}(answer_set,{index})") for index in range(len(constraints) - 1)]
    return extended_program, selectors


def build_control_and_maps(
        extended_program: str,
        mus_predicate: str,
):
    control = clingo.Control(["--warn=none"])
    control.add(extended_program)
    control.ground([("base", [])])
    selector_to_literal = {}
    literal_to_selector = {}
    for atom in control.symbolic_atoms.by_signature(mus_predicate, 2):
        selector = GroundAtom.parse(str(atom.symbol))
        selector_to_literal[selector] = atom.literal
        literal_to_selector[atom.literal] = selector

    counter = 0
    for atom in control.symbolic_atoms.by_signature(mus_predicate, 0):
        assert counter == 0
        counter += 1

        class Stopper(clingo.Propagator):
            def init(self, init):
                program_literal = init.symbolic_atoms[clingo.Function(mus_predicate)].literal
                solver_literal = init.solver_literal(program_literal)
                init.add_watch(solver_literal)

            def propagate(self, ctl: clingo.PropagateControl, changes: Sequence[int]) -> None:
                assert len(changes) == 1
                ctl.add_clause(clause=[-changes[0]], tag=True)

        control.register_propagator(Stopper())

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
    if on_core.res is not None and (len(on_core.res) == 0 or on_core.res[-1] != -1):
        return [literal_to_selector[literal] for literal in on_core.res if literal in literal_to_selector]

def get_selectors(extended_program_, mus_predicate, all_selectors):
    control, selector_to_literal, literal_to_selector = build_control_and_maps(extended_program_, mus_predicate)
    selectors = all_selectors 
    # console.log(f"Initial check with {len(selectors)} selectors...")
    result = check(
        control=control,
        with_selectors=selectors,
        literal_to_selector=literal_to_selector,
        selector_to_literal=selector_to_literal,
    )
    if result is None:
        # console.log(f"  It's a free choice. Stop!")
        return []
    # console.log(f"  Shrink to {len(result)} selectors!")
    selectors = result

    with Progress(console=console, transient=True) as progress:
        task = progress.add_task("Searching MUS...", total=len(selectors))
        required_selectors = 0

        while required_selectors < len(selectors):
            # console.log(f"Flag {selectors[-1]} as required!")
            required_selectors += 1
            selectors.insert(0, selectors.pop())  # last selector is required... move it ahead
            # console.log(f"Check with {len(selectors)} selectors...")
            result = check(
                control=control,
                with_selectors=selectors,
                literal_to_selector=literal_to_selector,
                selector_to_literal=selector_to_literal,
            )
            assert result is not None
            # console.log(f"  Shrink to {len(result)} selectors!")
            progress.update(task, advance=len(selectors) - len(result))
            selectors = result

    # console.log(f"Terminate with {len(selectors)} selectors!")
    return selectors
            
@typeguard.typechecked
def get_mus_program(
    program: SymbolicProgram,
    answer_set: AnswerSet,
    query_atom: GroundAtom | tuple[GroundAtom, ...]
) -> Optional[SymbolicProgram]:

    extended_program, all_selectors = build_extended_program_and_possible_selectors(
        program, answer_set, query_atom, MUS_PREDICATE
    )
    selectors = get_selectors(extended_program, MUS_PREDICATE, all_selectors)
    return SymbolicProgram.parse(f"{extended_program}"), selectors



def print_with_title(title, value):
    console.print(f"[bold red]{title}:[/bold red]")

    if type(value)==list:
        for e in value:
            console.print(f"{e}")
    else:
        console.print(f"{value}")
    console.print(f"[bold red]-------------[/bold red]")
    

@typeguard.typechecked
def print_output(
        query_atom: GroundAtom,
        result: SymbolicProgram | None,
):
    console.print("[bold red]MUS PROGRAM:[/bold red]")
    if result is not None:
        console.print(f"% {query_atom} is explained by")
        console.print(f"{result}")
    else:
        console.print(f"% {query_atom} is a free choice")


@typeguard.typechecked
def print_selectors(
        selectors: list
):
    console.print("[bold red]SELECTORS:[/bold red]")
    if len(selectors)==0:
        console.print("%IS A FREE CHOICE")
        return 
    for s in selectors:
        console.print(answer_set_element_to_string(s)+".")

def print_explanation(
        explanation: list[GroundAtom]
):
    console.print("[bold red]EXPLANATION:[/bold red]")
    for g in explanation:
        console.print(answer_set_element_to_string(g))

