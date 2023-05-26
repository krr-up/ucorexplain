import clingo
from clingo.ast import Transformer, parse_string
from clingo import ast as _ast
from typing import List, Tuple


RULE_ID_SIGNATURE = "_rule"


class RuleTransformer(Transformer):

    def __init__(self):
        self.rule_id = 0

    def visit_Rule(self, node):
        # add for each rule a theory atom (RULE_ID_SIGNATURE) with the id as an argument
        symbol = _ast.Function(
            location=node.location,
            name=RULE_ID_SIGNATURE,
            arguments=[_ast.SymbolicTerm(node.location, clingo.parse_term(str(self.rule_id)))],
            external=0)

        # increase the rule_id by one after every transformed rule
        self.rule_id += 1

        # insert id symbol into body of rule
        node.body.insert(len(node.body), symbol)
        return node.update(**self.visit_children(node))

    def get_transformed(self, program_string: str) -> str:
        self.rule_id = 1
        out = []
        parse_string(program_string, lambda stm: out.append((str(self(stm)))))
        out.append(f"{{_rule(1..{self.rule_id})}} % Choice rule to allow all _rule atoms to become assumptions")
        return "\n".join(out)

    # TODO : Not a nice implementation. Should be refined in the future
    def get_assumptions(self) -> List[Tuple[clingo.Symbol, bool]]:
        return [(clingo.parse_term(f"{RULE_ID_SIGNATURE}({rule_id})"), True) for rule_id in range(1, self.rule_id)]
