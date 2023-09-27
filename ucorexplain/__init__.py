"""
UCOREXPLAIN
"""


from typing import Final, Optional, Sequence, Union

import clingo
import typeguard
from dumbo_asp.primitives import (
    GroundAtom,
    Model,
    SymbolicAtom,
    SymbolicProgram,
    SymbolicRule,
    Predicate
)
from dumbo_utils.console import console
from rich.progress import Progress

AnswerSetElement = Union[GroundAtom, tuple[GroundAtom, bool]]
AnswerSet = tuple[AnswerSetElement, ...]

MUS_PREDICATE: Final = f"__mus__"


def unpack_answer_set_element(element: AnswerSetElement) -> tuple[GroundAtom, bool]:
    if type(element) != GroundAtom:
        return element
    return element, True


def answer_set_element_to_string(element: AnswerSetElement, *, flip: bool = False) -> str:
    if type(element) == GroundAtom:
        element = (element, True)
    return f"{'' if element[1] != flip else 'not '}{element[0]}"


def move_up(answer_set: AnswerSet, *pattern: SymbolicAtom) -> AnswerSet:
    def key(element):
        atom, truth_value = unpack_answer_set_element(element)
        return 0 if SymbolicAtom.of_ground_atom(atom).match(*pattern) else 1

    return tuple(sorted(answer_set, key=key))


def program_from_files(files) -> SymbolicProgram:
    prg_str = ""
    for f in files:
        with open(f) as f:
            prg_str += "".join(f.readlines())
    return SymbolicProgram.parse(prg_str)


def answer_set_to_constraints(
    answer_set: AnswerSet,
    query_atom: GroundAtom | tuple[GroundAtom, ...],
    mus_predicate: str,
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
            query_literals.append(answer_set_element_to_string(element, flip=False))
            query_atoms.remove(atom)
        else:
            constraints.append(
                f":- {answer_set_element_to_string(element, flip=True)}, {mus_predicate}(answer_set,{len(constraints)})"
                f"  %* Answer set *% ."
            )
    for atom in query_atoms:
        query_literals.append(answer_set_element_to_string(atom, flip=True))

    return [SymbolicRule.parse(constraint) for constraint in constraints] + [
        SymbolicRule.parse(f"{mus_predicate} :- {', '.join(query_literals)}.")
    ]


def build_extended_program_and_possible_selectors(
    program: SymbolicProgram,
    answer_set: AnswerSet,
    query_atom: GroundAtom | tuple[GroundAtom, ...],
    mus_predicate: str,
) -> tuple[SymbolicProgram, list[GroundAtom]]:
    rules = [
        rule.with_extended_body(SymbolicAtom.parse(f"{mus_predicate}(program,{index})"))
        for index, rule in enumerate(program)
    ]

    false_predicate: Final = Predicate.false().name
    atoms_in_the_answer_set = set(element if type(element) is GroundAtom else element[0] for element in answer_set)

    constraints = answer_set_to_constraints(answer_set, query_atom, mus_predicate)
    extended_program = SymbolicProgram.of(
        rules,
        constraints,
        SymbolicRule.parse(
            "{"
            + f"{mus_predicate}(program,0..{len(rules) - 1})"
            + (
                f"; {mus_predicate}(answer_set,0..{len(constraints) - 2})"
                if len(constraints) > 1
                else ""
            )
            + "}."
        ),
        # MALVI: WE STILL NEED SOMETHING FROM to_zero_simplification_version()
        SymbolicRule.parse(' | '.join(str(atom) for atom in atoms_in_the_answer_set) + f" :- {false_predicate}."),
        SymbolicRule.parse(f"{{{false_predicate}}}."),
        SymbolicRule.parse(f":- {false_predicate}."),
    )
    selectors = [
        GroundAtom.parse(f"{mus_predicate}(program,{index})")
        for index in range(len(rules))
    ] + [
        GroundAtom.parse(f"{mus_predicate}(answer_set,{index})")
        for index in range(len(constraints) - 1)
    ]
    print_with_title("EXTENDED PROGRAM", extended_program)

    return extended_program, selectors


def build_control_and_maps(
    extended_program: str,
    mus_predicate: str,
):
    # SHOULD WE GO FOR PROPAGATION RULES USED FOR COMPUTING SUPPORT MODELS? THAT IS, WE DON'T WANT TO USE WELL FOUNDED COMPUTATION...
    control = clingo.Control(["--supp-models", "--no-ufs-check", "--sat-prepro=no", "--eq=0", "--no-backprop"])
    # control = clingo.Control()
    control.add(str(extended_program))
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
                program_literal = init.symbolic_atoms[
                    clingo.Function(mus_predicate)
                ].literal
                solver_literal = init.solver_literal(program_literal)
                init.add_watch(solver_literal)

            def propagate(
                self, ctl: clingo.PropagateControl, changes: Sequence[int]
            ) -> None:
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
    control.solve(
        assumptions=[selector_to_literal[selector] for selector in with_selectors]
        + [-1],
        on_core=on_core,
    )
    if on_core.res is not None and (len(on_core.res) == 0 or on_core.res[-1] != -1):
        return [
            literal_to_selector[literal]
            for literal in on_core.res
            if literal in literal_to_selector
        ]


def get_selectors(extended_program_, mus_predicate, all_selectors):
    control, selector_to_literal, literal_to_selector = build_control_and_maps(
        extended_program_, mus_predicate
    )
    selectors = all_selectors
    result = check(
        control=control,
        with_selectors=selectors,
        literal_to_selector=literal_to_selector,
        selector_to_literal=selector_to_literal,
    )
    if result is None:
        selectors = []
        print_with_title("SELECTORS", selectors)
        return selectors
    selectors = result

    required_selectors = 0
    while required_selectors < len(selectors):
        required_selectors += 1
        selectors.insert(
            0, selectors.pop()
        )  # last selector is required... move it ahead
        result = check(
            control=control,
            with_selectors=selectors,
            literal_to_selector=literal_to_selector,
            selector_to_literal=selector_to_literal,
        )
        assert result is not None
        selectors = result    

    print_with_title("SELECTORS", selectors)
    return selectors


def extend_program_with_externals(extended_program, herbrand):
    """
    Extends the program with the atoms in the herbrand as externals to avoid simplifications
    """
    herbrand_as_externals = "\n" + "\n".join(f"#external {str(h)}." for h in herbrand)
    extended_program_with_externals = str(extended_program) + herbrand_as_externals
    print_with_title("EXTENDED PROGRAM WITH EXTERNALS", extended_program_with_externals)
    return extended_program_with_externals


def extend_answer_set(answer_set, herbrand):
    """
    Extends an answer set with (a, False) for every a in herbrand that is not in defined
    """
    atoms_in_answer_set = set(element[0] for element in answer_set)
    answer_set = list(answer_set)
    for atom in herbrand:
        if atom not in atoms_in_answer_set:
            answer_set.append((atom, False))
    return tuple(answer_set)


def get_answer_set(answer_set_str):
    """
    Gets and answer set of tuples (Atom, Truth) from a string
    """
    answer_set = []
    if answer_set_str == "":
        return tuple([])
    for atom in answer_set_str.split(" "):
        answer_set.append(
            (GroundAtom.parse(atom[1:]), False)
            if atom.startswith("~")
            else (GroundAtom.parse(atom), True)
        )
    return tuple(answer_set)


def get_herbrand_choices(program, known_atoms):
    """
    Adds choices for the known atoms and computes the herbrand base
    """
    choices = [SymbolicRule.parse("{" + str(a) + "}.") for a in known_atoms]
    print_with_title("CHOICES", choices)
    program_with_choices = SymbolicProgram.parse(
        str(program) + "\n" + "".join([str(c) + "\n" for c in choices])
    )
    herbrand = program_with_choices.herbrand_base
    print_with_title("HERBRAND BASE", herbrand)
    return herbrand

def get_herbrand_zero(program, known_atoms, compact=True):
    """
    Adds choices for the known atoms and computes the herbrand base
    """
    program_with_false = program.to_zero_simplification_version(
        extra_atoms=known_atoms,
        compact=compact
    )
    print_with_title("PROGRAM WITH FALSE", program_with_false)
    herbrand = program_with_false.herbrand_base_without_false_predicate
    print_with_title("HERBRAND BASE", herbrand)
    return herbrand

def remove_false(extended_program):
    """
    Removes rules using __false__ added in the build_extended_program_and_possible_selectors method
    This is just the last three rules that are added.
    """
    return SymbolicProgram.of([rule for rule in extended_program][:-3])  # MALVI: DISCARD rules with __false__

def get_reified_program(prg):
    reify_program = program_from_files(["ucorexplain/encodings/mario_reify.lp"])
    full_prg = SymbolicProgram.of(*reify_program, *prg)
    reified_program = Model.of_program(full_prg).as_facts
    return reified_program

def get_serialization_program(expanded_prg, query_atom):
    expanded_prg_facts = Model.of_atoms(expanded_prg.serialize(base64_encode=False)).as_facts
    expanded_prg_program = SymbolicProgram.parse(expanded_prg_facts)
    query_program = SymbolicProgram.parse(f'query({clingo.String(str(query_atom))}).')
    serialization_program = SymbolicProgram.of(*expanded_prg_program, *query_program)
    print_with_title("SERIALIZATION PROGRAM", serialization_program)

    return serialization_program

def get_derivation_sequence_program(reified_program):
    derivation_sequence = []
    ctl = clingo.Control(["1"])
    ctl.load("ucorexplain/encodings/mario_meta.lp")
    ctl.add("base",[],reified_program)
    ctl.ground([("base", [])])
    def m(atoms):
        for atom in atoms.symbols(shown=True):
            at = GroundAtom.parse(str(atom))
            derivation_sequence.append(f"{at.predicate_name}({','.join(str(arg) for arg in at.arguments)},{len(derivation_sequence) + 1})")
    ctl.solve(on_model=m)

    derivation_sequence_prg = SymbolicProgram.parse(Model.of_atoms(derivation_sequence).as_facts)
    # WARNING! Here I'm assuming that atoms are ordered according to the derivation in the solver. If it is not, we need a propagator or something different
    print_with_title("DERIVATION SEQUENCE", derivation_sequence_prg)
    
    return derivation_sequence_prg

def get_graph(derivation_sequence_prg, serialization_program):
    graph_program = program_from_files(["ucorexplain/encodings/mario_graph.lp"])
    compute_graph_prg = SymbolicProgram.of(*graph_program, *derivation_sequence_prg, *serialization_program)

    graph = Model.of_program(compute_graph_prg)
    graph = graph.filter(when=lambda atom: atom.predicate_name in ["node", "link'"])
    graph = graph.rename(Predicate.parse("link'"), Predicate.parse("link"))
    print_with_title("GRAPH", derivation_sequence_prg)

    return graph

def print_with_title(title, value):
    console.print(f"[bold red]{title}:[/bold red]")

    if type(value) == list:
        for e in value:
            console.print(f"{e}")
    else:
        console.print(f"{value}")
    console.print(f"[bold red]-------------[/bold red]")


@typeguard.typechecked
def print_output(query_atom: GroundAtom, result: SymbolicProgram | None):
    console.print("[bold red]MUS PROGRAM:[/bold red]")
    if result is not None:
        console.print(f"% {query_atom} is explained by")
        console.print(f"{result}")
    else:
        console.print(f"% {query_atom} is a free choice")


@typeguard.typechecked
def print_selectors(selectors: list):
    console.print("[bold red]SELECTORS:[/bold red]")
    if len(selectors) == 0:
        console.print("%IS A FREE CHOICE")
        return
    for s in selectors:
        console.print(answer_set_element_to_string(s) + ".")


def print_explanation(explanation: list[GroundAtom]):
    console.print("[bold red]EXPLANATION:[/bold red]")
    for g in explanation:
        console.print(answer_set_element_to_string(g))


@typeguard.typechecked
def get_mus_program_and_selectors(
    program: SymbolicProgram,
    answer_set: AnswerSet,
    query_atom: GroundAtom | tuple[GroundAtom, ...],
) -> Optional[SymbolicProgram]:
    """
    Builds MUS program extended with  with externals and the needed selectors
    """
    atoms_in_answer_set = set(element[0] for element in answer_set)
    
    
    # Get full herbrand based on query and answer
    # full_query = list(query_atom) if type(query_atom) == tuple else [query_atom]
    # known_atoms = set(list(atoms_in_answer_set) + full_query) # PREVIOUS VERSION
    # herbrand = get_herbrand_choice(program, known_atoms)# PREVIOUS VERSION

    herbrand_base = get_herbrand_zero(program, atoms_in_answer_set)

    # Add atoms from herbrand to answer set
    answer_set = extend_answer_set(answer_set, herbrand_base)

    # Get MUS program
    extended_program, all_selectors = build_extended_program_and_possible_selectors(
        program, answer_set, query_atom, MUS_PREDICATE
    )

    # extended_program_with_externals = extend_program_with_externals(
    #     extended_program, herbrand
    # ) # PREVIOUS VERSION

    selectors = get_selectors(
        extended_program, MUS_PREDICATE, all_selectors
    )

    # Remove __false__ from rules
    extended_program = remove_false(extended_program)

    return extended_program, selectors
