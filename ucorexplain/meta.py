# from typing import List, Optional

# from clingo import Control, Symbol
# from clingox.reify import Reifier
# from dumbo_asp.primitives import GroundAtom

# from ucorexplain import print_with_title


# def reify(prg: Optional[str] = None, files: Optional[List] = None) -> str:
#     """
#     Reifies the program and files provided

#         Returns: a string representing the reified program
#     """
#     if files is None:
#         files = []
#     symbols: List[Symbol] = []
#     ctl = Control(["--warn=none"])
#     reifier = Reifier(symbols.append, reify_steps=False)
#     ctl.register_observer(reifier)
#     if prg is not None:
#         ctl.add("base", [], str(prg))
#     for f in files:
#         ctl.load(f)
#     ctl.ground([("base", [])])
#     rprg = "\n".join([str(s) + "." for s in symbols])
#     return rprg


# def run_meta(mus_prg, selectors, i=3):
#     reified = reify(prg=str(mus_prg))
#     ctl = Control(["--warn=none", f"-c i={i}"])
#     selectors_program = "\n".join(f"__core__({selector})." for selector in selectors)

#     ctl.add("base", [], selectors_program)
#     ctl.add("base", [], reified)
#     ctl.load("ucorexplain/encodings/inf_meta.lp")

#     ctl.ground([("base", [])])
#     explanations = []

#     def on_model(m):
#         explanations.append([GroundAtom.parse(str(s)) for s in m.symbols(shown=True)])

#     ctl.solve(on_model=on_model)
#     explanation = []
#     if len(explanations) > 0:
#         explanation = explanations[0]
#     print_with_title("EXPLANATION", explanation)
#     return explanation
