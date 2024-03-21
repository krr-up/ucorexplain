from dataclasses import dataclass
from typing import Tuple

import clingo
import clorm.orm.core
from clingraph import Factbase


def split_tuple_string(string: str) -> Tuple[str, str]:
    level = 0
    left = []
    right = []
    current = left
    for char in string:
        if level == 1 and char == ",":
            current = right
            continue
        if char == "(":
            level += 1
            if level == 1:
                continue
        if char == ")":
            level -= 1
            if level == 0:
                continue
        current.append(char)
    return "".join(left), "".join(right)


@dataclass
class TextNode:
    name: str
    reason: str
    rule: str


def expand_node(node: str, edges, associated_reasons, associated_rules):
    node_object = TextNode(
        name=node,
        reason=associated_reasons.get(node),
        rule=associated_rules.get(node),
    )
    if node in edges:
        return [node_object, *[expand_node(edge, edges, associated_reasons, associated_rules) for edge in edges[node]]]
    return [node_object]


def print_nested(nested_list, level=0):
    for elem in nested_list:
        if isinstance(elem, list):
            print_nested(elem, level + 1)
        else:
            print(level * "-" + str(elem))


def textualize_clingraph_factbase(factbase: Factbase) -> None:
    clorm_fb = factbase.fb
    fb_nodes = list(clorm_fb.query(factbase.Node).all())
    fb_edges = list(clorm_fb.query(factbase.Edge).all())
    edges = {}
    node_lookup = {}
    for n in fb_nodes:
        node, parent = split_tuple_string(str(n.id))
        node_lookup[str(n.id)] = node
        if parent in edges:
            edges[parent].add(node_lookup[str(n.id)])
        else:
            edges[parent] = {node_lookup[str(n.id)]}
    # this step is redundant if each node has only one incoming edge
    for e in fb_edges:
        n1, n2 = split_tuple_string(str(e.id))
        parent = node_lookup[n1]
        node = node_lookup[n2]
        if parent in edges:
            edges[parent].add(node)
        else:
            edges[parent] = {node}
    # -----
    print(factbase)
    print("-" * 60)
    reasons = clorm_fb.query(factbase.Attr).where(
        factbase.Attr.element_type == "node",
        factbase.Attr.attr_id[0] == "label",
        factbase.Attr.attr_id[1] == clorm.orm.core.Raw(clingo.parse_term("reason")),
    ).select(factbase.Attr.element_id, factbase.Attr.attr_value).all()
    rules = clorm_fb.query(factbase.Attr).where(
        factbase.Attr.element_type == "node",
        factbase.Attr.attr_id[0] == "label",
        factbase.Attr.attr_id[1] == clorm.orm.core.Raw(clingo.parse_term("rule")),
    ).select(factbase.Attr.element_id, factbase.Attr.attr_value).all()
    print(node_lookup)
    reasons = {node_lookup[str(node)]: reason for node, reason in reasons}
    rules = {node_lookup[str(node)]: rule for node, rule in rules}
    print("REASONS", reasons)
    print("RULES", rules)
    print("-" * 60)
    # -----
    nested = expand_node("root", edges, reasons, rules)
    print_nested(nested)
