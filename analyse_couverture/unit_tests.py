import unittest

from ast_to_cfg import AstToCfgConverter
from ast_tree import GeneratorAstTree
from process_tests import process_value_test


class TestAstToCfgMethods(unittest.TestCase):
    def test_childrenAreCstOrVar(self):
        if_tree = GeneratorAstTree.create_if_cfg()
        body_part = if_tree.children[1]
        self.assertEqual(AstToCfgConverter.check_children_are_cst_or_var(if_tree), False)
        self.assertEqual(AstToCfgConverter.check_children_are_cst_or_var(body_part), True)

    def test_treat_while_node(self):
        # test simple while loop
        while_tree = GeneratorAstTree.create_basic_while_tree()
        parser = AstToCfgConverter(while_tree)
        result = parser.treat_while_node(while_tree)
        expected = {
            1: ['while', '<', ['x', 5], [2, 3]],
            2: ['assign', {'x': 'x+1'}, 1],
        }
        self.assertEqual(result, expected)

        # test tree with sequence inside
        while_tree_seq = GeneratorAstTree.while_tree_with_sequence()
        parser2 = AstToCfgConverter(while_tree_seq)
        result2 = parser2.treat_while_node(while_tree_seq)

        expected2 = {
            1: ["while", '<', ['x', 5], [2, 4]],
            2: ['assign', {'x': 'x+x'}, 3],
            3: ['assign', {'x': 'x-1'}, 1]
        }

        self.assertEqual(result2, expected2)

    def test_treat_seq_node(self):
        prog_tree = GeneratorAstTree.create_prog_tree()
        parser = AstToCfgConverter(prog_tree)
        result = parser.treat_seq_node(prog_tree)
        expected = {
            1: ['if', '<=', ["x", 0], [2, 3]],
            2: ['assign', {'x': '0-x'}, 4],
            3: ['assign', {'x': '1-x'}, 4],
            4: ['if', '==', ["x", 1], [5, 6]],
            5: ['assign', {'x': '1'}, 7],
            6: ['assign', {'x': 'x+1'}, 7]
        }
        self.assertEqual(result, expected)

    def test_treat_if_node(self):
        basic_if_tree = GeneratorAstTree.create_if_cfg()
        if_tree_with_seq = GeneratorAstTree.create_if_cfg_else_is_seq()
        parser = AstToCfgConverter(if_tree_with_seq)
        result = parser.treat_if_node(if_tree_with_seq)

        parser_for_basic = AstToCfgConverter(basic_if_tree)
        result_for_basic = parser_for_basic.treat_if_node(basic_if_tree)

        expected = {
            1: ['if', '==', ["x", 1], [2, 3]],
            2: ['assign', {'x': '1'}, 5],
            3: ['assign', {'x': '32'}, 4],
            4: ['assign', {'x': 'x*4'}, 5]
        }

        expected_basic = {
            1: ['if', '==', ["x", 1], [2, 3]],
            2: ['assign', {'x': '1'}, 4],
            3: ['assign', {'x': 'x+1'}, 4]
        }

        self.assertEqual(result, expected)
        self.assertEqual(result_for_basic, expected_basic)

    def test_get_height(self):
        prog_tree = GeneratorAstTree.create_prog_tree()
        basic_if_tree = GeneratorAstTree.create_if_cfg()
        h_prog = prog_tree.get_height()
        h_if = basic_if_tree.get_height()
        self.assertEqual(h_prog, 4)
        self.assertEqual(h_if, 3)

    def test_get_cfg_graph(self):
        assign_prog = GeneratorAstTree.create_test_assign()
        parser = AstToCfgConverter(assign_prog)
        result = parser.get_cfg_graph()
        expected = {
            1: ['if', '<=', ['x', 0], [2, 3]],
            2: ['assign', {'y': 'x'}, 4],
            3: ['assign', {'y': '0-x'}, 4],
            4: ['assign', {'x': 'y*2'}, 0]
        }

        self.assertEqual(result, expected)


class TestProcessTestsMethods(unittest.TestCase):
    def test_process_value_test(self):
        graph_prog = {
            1: ['if', '<=', ["x", 0], [2, 3]],
            2: ['assign', {'x': '0-x'}, 4],
            3: ['assign', {'x': '1-x'}, 4],
            4: ['if', '==', ["x", 1], [5, 6]],
            5: ['assign', {'x': '1'}, 0],
            6: ['assign', {'x': 'x+1'}, 0]
        }
        result_path, result_var = process_value_test(3, graph_prog, {})
        self.assertEqual(result_var['x'], -1)
        result_path, result_var = process_value_test(-1, graph_prog, {})
        self.assertEqual(result_var['x'], 1)


if __name__ == "__main__":
    unittest.main()
