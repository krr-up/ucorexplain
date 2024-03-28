from dataclasses import dataclass
from typing import Tuple, List
from pathlib import Path

import clingo
import clorm.orm.core
from clingraph import Factbase
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree
from textual.widgets.tree import TreeNode
from rich.text import Text

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


def textualize_clingraph_factbase(factbase: Factbase, expand_depth: int) -> None:
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
    reasons = {node_lookup[str(node)]: reason for node, reason in reasons}
    rules = {node_lookup[str(node)]: rule for node, rule in rules}
    # -----
    nested = expand_node("root", edges, reasons, rules)

    app = TextTreeApp(nested, expand_depth=expand_depth)
    app.run()


class TextTreeApp(App):
    """A textual app to show the explanation forrest in an interactive tree view in the terminal"""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"),
                ("x", "exit", "Exit")]

    def __init__(self, data: List, expand_depth: int):
        super(TextTreeApp, self).__init__()
        self.data = data
        self.expand_depth = expand_depth

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        t = Tree("Explanation Tree", id="explanation-tree")
        self.build_tree(t.root, self.data, auto_expand_level=self.expand_depth)
        t.root.expand()
        yield t

    @staticmethod
    def build_tree(node: TreeNode, nested_list: List, level: int = 0, auto_expand_level: int = 2) -> None:
        new_node = None
        for elem in nested_list:
            if isinstance(elem, list):
                TextTreeApp.build_tree(new_node, elem, level + 1, auto_expand_level=auto_expand_level)
            else:
                if elem.name == "root":
                    # skip root node
                    new_node = node
                else:
                    new_node = node.add(elem.name)
                    if level <= auto_expand_level:
                        new_node.expand()
                    reason_string = str(elem.reason).replace('"', "")
                    rule_string = str(elem.rule).replace('"', "")
                    reason = new_node.add_leaf(f"Reason: {reason_string}")
                    rule = new_node.add_leaf(f"Rule: {rule_string}")
                    reason.label.stylize("bold #0087D7", 0, 7)
                    rule.label.stylize("bold #0087D7", 0, 5)
                    rule.label.stylize("#888888", 6)

    def action_exit(self):
        self.exit()

    def action_add(self):
        tree = self.query_one(Tree)
        tree.root.add("TEST")

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
