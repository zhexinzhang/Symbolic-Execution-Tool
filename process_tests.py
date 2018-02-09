#!/usr/bin/env python
# -*- coding: utf-8 -*-

LIMIT_FOR_INFINITE_LOOP = 100


def process_value_test(graph, variables):
    """
    :param graph: CFG graph
    :param variables: a dictionary {var: initial_value}
    :return: steps the program went through, dic of final values of variables
    """
    path = []
    next_node = 1
    path.append(next_node)
    count = 0
    while next_node != 0 and count <= LIMIT_FOR_INFINITE_LOOP:
        if count == LIMIT_FOR_INFINITE_LOOP:
            raise ValueError('Infinite loop - program stopped')

        node = graph[next_node]
        if node[0] == "if" or node[0] == "while":
            bool_result = process_bool_expression(node[1], variables)  # check condition, returns True or False
            next_node = node[-1][0] if bool_result else node[-1][1]
        elif node[0] == "skip":
            next_node = node[1][0]
        elif node[0] == "assign":
            instruct = node[1]
            for key, instruction in instruct.items():
                variables[key] = eval(replace_any_var_by_value(instruction, variables))
            next_node = node[2][0]

        path.append(next_node)
        count += 1
    return path, variables


def process_bool_expression(conditions, variables):
    """

    :param conditions: [[(comp1), (comp2)],[(comp3), (comp4)]], each element is a list of conditions that
    must be respected (and logical gate)
    :param variables:
    :return:
    """
    result = True
    # we want AND between each condition
    # -> if any of the condition is false, the result is false
    if any(not process_or_expression(condition, variables) for condition in conditions):
        result = False

    return result


def process_or_expression(conditions, variables):
    result = False
    # we want a OR between each condition
    # -> if only one condition is true, the result is true
    if any(process_condition(condition, variables) for condition in conditions):
        result = True

    return result


def process_condition(comparison, variables):
    # comparison : tuple ('<=', ['x', 0])
    operator = comparison[0]
    values = comparison[1]

    # if variable in variable, pass its value, else pass the value
    # there will be an error if the variable given isn't inside the dictionary of variables
    return compare(
        operator,
        variables[values[0]] if values[0] in variables else values[0],
        variables[values[1]] if values[1] in variables else values[1],
    )


def compare(operator, a, b):
    if operator == "<=":
        if a <= b:
            return True
        else:
            return False
    elif operator == "<":
        if a < b:
            return True
        else:
            return False
    elif operator == "==":
        if a == b:
            return True
        else:
            return False
    elif operator == ">":
        if a > b:
            return True
        else:
            return False
    elif operator == ">=":
        if a >= b:
            return True
        else:
            return False
    elif operator == "!=":
        if a != b:
            return True
        else:
            return False


def get_all_paths(graph, start, path=None):
    if path is None:
        path = []

    if start == 0:
        # end of graph
        return [path + [start]]

    path = path + [start]

    if start not in graph:
        return []

    paths = []
    for node in graph[start][-1]:
        if node not in path:
            new_paths = get_all_paths(graph, node, path)
            for new_path in new_paths:
                paths.append(new_path)
    return paths


def replace_any_var_by_value(instruction, variables):
    for key, value in variables.items():
        instruction = instruction.replace(key, str(value))
    return instruction


def get_all_def(graph):
    """
    Returns a list of step that are assignments (definition) in a CFG
    :param graph:
    :return: list
    """
    variables = get_all_var(graph)
    steps = []
    for variable in variables:
        steps.extend(get_definition_for_variable(graph, variable))

    return steps


def get_definition_for_variable(graph, variable):
    """
    Returns a list of step that are assignments (definition) in a CFG for a given variable
    :param graph:
    :param variable:
    :return: list
    """
    steps = []
    for key, value in graph.items():
        if is_def(value, variable):
            steps.append(key)
    return steps


def get_all_var(graph):
    """
    returns the list of variable assigned/used in a program from a given CFG
    :param graph:
    :return: list
    """
    variables = []
    for node, value in graph.items():
        if any(value[0] == x for x in ('while', 'if')):
            variables.extend(get_var_from_bool_expr(value[1]))
        if value[0] == 'assign':
            variables.extend(list(value[1].keys()))

    return variables


def is_def(node, variable):
    if node[0] != 'assign':
        return False

    if variable in node[1]:
        return True
    else:
        return False


def is_ref(node, variable):
    if node[0] == 'while' or node[0] == 'if':
        if variable in get_var_from_bool_expr(node[1]):
            return True
        else:
            return False
    elif node[0] == 'assign':

        if variable in node[1].values():
            return True
        else:
            return False
    else:
        return False


def get_var_from_bool_expr(expression):
    variables = []
    for or_expr in expression:
        for condition in or_expr:
            for value in condition[1]:
                if isinstance(value, str):
                    variables.append(value)

    return variables


def all_affectations(values_test, graph):
    print("\n ------")
    print("Criterion: all affectations")

    objective = []
    for key, value in graph.items():
        if value[0] == "assign":
            objective.append(key)

    print("We want the following nodes to be visited: " + str(objective))

    for value in values_test:
        path, var = process_value_test(graph, value)
        for step in path:
            if step in objective:
                objective.remove(step)
    
    if len(objective) == 0:
        print("TA: OK")
    else:
        print("TA fails:")
        print("Nodes " + str(objective) + " were never reached.")


def all_decisions(values_test, graph):
    print("\n ------")
    print("Criterion: all decisions")

    objective = []
    for key, value in graph.items():
        if value[0] == "if" or value[0] == "while":
            objective.append(key)
            for following_nodes in value[-1]:
                objective.append(following_nodes)

    print("We want the following nodes to be visited: " + str(objective))

    for value in values_test:
        path, var = process_value_test(graph, value)
        for step in path:
            if step in objective:
                objective.remove(step)
    
    if len(objective) == 0:
        print("TD: OK")
    else:
        print("TD fails:")
        print("Nodes " + str(objective) + " were never reached.")


def all_k_paths(values_test, graph, k):
    print("\n ------")
    print("Criterion: all k paths for k = " + str(k))

    all_paths = get_all_paths(graph, 1)

    target_paths = []
    for path in all_paths:
        if not path[:k] in target_paths:
            target_paths.append(path[:k])

    print("We want the following paths to be taken: " + str(target_paths))

    for value in values_test:
        path, var = process_value_test(graph, value)
        # print("path for value " + str(value) + " : " + str(path))
        if path[:k] in target_paths:
            target_paths.remove(path[:k])

    if len(target_paths) == 0:
        print("All k paths for k = " + str(k) + ": OK")
    else:
        print("All k paths for k = " + str(k) + " fails:")
        print("Paths " + str(target_paths) + " were never taken entirely.")


def all_i_loops(values_test, graph, k):
    # TODO: check the condition i loop: the a loop must be visited at must i times,
    #  but for every test value or for all the data set ?
    print("\n ------")
    print("Criterion: all i loops")

    objective = []
    for key, value in graph.items():
        if value[0] == "while":
            objective.append(value[-1][0])

    print("We want the following nodes " + str(objective) + " to be visited. (At must " + str(k) + " times.)")

    count_dic = {obj: 0 for obj in objective}

    for value in values_test:
        path, var = process_value_test(graph, value)
        for step in path:
            if step in objective:
                count_dic[step] += 1

    if all(k >= value > 0 for step, value in count_dic.items()):
        print(str(k) + "-TB: OK")
    else:
        print(str(k) + "-TB fails:")
        if any(value > k for step, value in count_dic.items()):
            print("One or more while loop was visited more than " + str(k) + " time.")
        if any(value == 0 for step, value in count_dic.items()):
            print("On or more while loop was never visited.")


def all_definitions(values_test, graph):
    # Todo
    # interpretation : for every definition, there is a path from the affection to its utilization.
    pass


def read_test_file(path_tests):
    values_tests = []
    with open(path_tests) as file:
        for line in file:
            variables = {}
            assignments = line.split(",")
            for assignment in assignments:
                var = assignment.split(":")[0]
                value = assignment.split(":")[1]
                variables[var] = int(value)
            values_tests.append(variables)
    return values_tests


if __name__ == '__main__':

    PATH_TESTS = "sets_tests_txt/test.txt"

    # Hand written CFG graphs
    # (temporary - while ast_to_cfg isn't connected to process_tests)

    test_two_variables = {
        1: ['if', [[('<=', ['x', 0])]], [2, 3]],
        2: ['assign', {'y': 'x'}, [4]],
        3: ['assign', {'y': '0-x'}, [4]],
        4: ['assign', {'x': 'y*2'}, [0]]
    }

    graph_prog = {
            1: ['if', [[('<=', ["x", 0])]], [2, 3]],
            2: ['assign', {'x': '0-x'}, [4]],
            3: ['assign', {'x': '1-x'}, [4]],
            4: ['if', [[('==', ["x", 1])]], [5, 6]],
            5: ['assign', {'x': '1'}, [0]],
            6: ['assign', {'x': 'x+1'}, [0]]
    }

    graph_factorial = {
        1: ['assign', {'n': '1'}, [2]],
        2: ['while', [[('>=', ['x', 1])]], [3, 0]],
        3: ['assign', {'n': 'n*x'}, [4]],
        4: ['assign', {'x': 'x-1'}, [2]]
    }

    test_values = read_test_file(PATH_TESTS)
    all_affectations(test_values, test_two_variables)
    test_values = read_test_file(PATH_TESTS)
    all_decisions(test_values, test_two_variables)
    test_values = read_test_file(PATH_TESTS)
    all_affectations(test_values, graph_prog)
    test_values = read_test_file(PATH_TESTS)
    all_decisions(test_values, graph_prog)
    test_values = read_test_file(PATH_TESTS)
    all_k_paths(test_values, graph_prog, 3)
    test_values = read_test_file(PATH_TESTS)
    all_k_paths(test_values, graph_prog, 5)
    test_values = read_test_file(PATH_TESTS)
    all_k_paths(test_values, test_two_variables, 3)
    test_values = read_test_file(PATH_TESTS)
    all_k_paths(test_values, test_two_variables, 5)

    test_values = read_test_file("sets_tests_txt/tests_for_fact.txt")
    all_affectations(test_values, graph_factorial)

    test_values = read_test_file("sets_tests_txt/tests_for_fact.txt")
    all_i_loops(test_values, graph_factorial, 2)

    test_values = read_test_file('sets_tests_txt/tests2.txt')
    all_i_loops(test_values, graph_factorial, 2)
