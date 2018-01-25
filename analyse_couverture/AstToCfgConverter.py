"""
CFG Graph Structure:
The graph is a dictionary.
Key is the numeration of the node
Value is a tuple containing instructions
tuple[0] contains the command type:
it can be "assign", "while", "if" or "skip"

***** For "if" and "while" commands:
tuple[1] is the comparator it can be "<=" to ">="
tuple[2] is a list of values used to operate the
operator given in tuple[1]. It's a length 2 list, with
list[0] the first value to be compared,
and list[1] the second value
these two can either be a string ("x" or "y") or an int

****** ******* TODO add ability to compare y without comparing x
If the list is length 2, the first value will be checked 
against the second
tuple[3] contains a tuple of 2 elements.
The first one is the following node when the
statement is true, the second one the following node when the 
statement is false.

***** For "assign" commands:
tuple[1] is the new value of the first variable x
it reads like : x = tuple[1]
tuple[2] is the new value of the second variable y
it reads like y = tuple[2]
tuple[3] is the following node

***** For "skip" commands:
tuple[1] is the following node

Example graph for "prog" program:
graph_prog = {
    1: ("if", "<=", ["x", 0], (2, 3)),
    2: ("assign", "-x", "", 4),
    3: ("assign", "1-x", "", 4),
    4: ("if", "==", ["x", 1], (5, 6)),
    5: ("assign", "1", "", 0),
    6: ("assign", "x+1", "", 0)
}

"""


class AstToCfgConverter(object):
    def __init__(self, ast_tree):
        self.ast_tree = ast_tree
        self.step = 1

    def treat_seq_node(self, node):
        full_graph = {}
        for child in node.children:
            if child.category == "if":
                partial_graph = self.treat_if_node(child)
                full_graph.update(partial_graph)
                self.step += 1
            elif child.category == "assign":
                tmp = self.treat_assign_node(child)  # ["x+1", ""]
                # 2: ("assign", "-x", "", 4),
                partial_graph = {
                    self.step: ("assign", tmp[0], tmp[1], self.step + 1)
                }
                full_graph.update(partial_graph)
                self.step += 1
            else:
                # TODO
                pass
        return full_graph

    def treat_if_node(self, node):
        operator = self.treat_compare_node(node.children[0])
        partial_graph = {self.step: ("if", operator[0], operator[1], (self.step+1, self.step+2))}

        delta = 1
        if node.children[1].category == "sequence":
            if delta < len(node.children[1].children):
                delta = len(node.children[1].children)
        if node.children[2].category == "sequence":
            if delta < len(node.children[2].children):
                delta = len(node.children[2].children)
        
        if node.children[1].category == "assign":
            self.step += 1
            if_body_assign = self.treat_assign_node(node.children[1])
            partial_graph[self.step] = ("assign", if_body_assign[0], if_body_assign[1], self.step + delta + 1)
        elif node.children[1].category == "sequence":
            self.step += 1
            seq = node.children[1]
            partial_graph.update(self.treat_seq_node(seq))
        else:
            # TODO
            pass

        if node.children[2].category == "assign":
            self.step += 1
            else_body_assign = self.treat_assign_node(node.children[2])
            partial_graph[self.step] = ("assign", else_body_assign[0], else_body_assign[1], self.step + delta)
        elif node.children[2].category == "sequence":
            self.step += 1
            seq = node.children[2]
            partial_graph.update(self.treat_seq_node(seq))
        else:
            # TODO
            pass

        return partial_graph

    @staticmethod
    def treat_compare_node(node):
        """
        Returns a list [operator(string), [constants]]
        """
        result = [node.data]  # append operator
        values = []

        for child in node.children:
            values.append(child.data)
        
        result.append(values)
        return result

    @staticmethod
    def treat_operation_node(node):
        """
        Returns a string containing the operation
        """
        return str(node.children[0].data) + node.data + str(node.children[1].data)

    @staticmethod
    def treat_assign_node(node):
        """
        Returns a list of two elements, the first one being the new affectation of X,
        the second one the new affectation of Y ("" is no new affectation)
        """
        result = []
        if node.children[0].category == "constant" or node.children[0].category == "variable":
            left_member_str = str(node.children[0].data)
        else:
            left_member_str = AstToCfgConverter.treat_operation_node(node.children[0])

        if node.children[1].category == "constant" or node.children[1].category == "variable":
            right_member_str = str(node.children[1].data)
        else:
            right_member_str = AstToCfgConverter.treat_operation_node(node.children[1])
        
        if left_member_str == "X" or left_member_str == "x":
            result.append(right_member_str)
            result.append("")
        else:
            result.append("")
            result.append(right_member_str)
        
        return result


def check_children_are_cst_or_var(node):
    for child in node.children:
        if child.category != "constant" and child.category != "variable":
            return False
    return True
