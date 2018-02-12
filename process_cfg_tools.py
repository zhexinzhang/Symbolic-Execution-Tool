#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module provides tools and functions in order to process a set of values on a program.
We expect a CFG graph for program processed and a dictionary of value for every variable of the program
"""

from constraint import *

LIMIT_FOR_INFINITE_LOOP = 100


def process_value_test(graph, variables, info_conditions=False):
    """
    :param graph: CFG graph
    :param variables: a dictionary {var: initial_value}
    :param info_conditions: a boolean, if true: will return an additional value which is a dic,
    stating how each condition was evaluated.
    :return: steps the program went through, dic of final values of variables
    """
    path = []
    next_node = 1
    path.append(next_node)
    count = 0

    dic_result_cond = {}

    while next_node != 0 and count <= LIMIT_FOR_INFINITE_LOOP:
        if count == LIMIT_FOR_INFINITE_LOOP:
            raise ValueError('Infinite loop - program stopped')

        node = graph[next_node]
        if type_node(node) == "if" or type_node(node) == "while":
            bool_result = process_bool_expression(node[1], variables)  # check condition, returns True or False

            if info_conditions:
                dic_result_cond[next_node] = analyze_conditions(node[1], variables)

            next_node = node[-1][0] if bool_result else node[-1][1]
        elif type_node(node) == "skip":
            next_node = node[1][0]
        elif type_node(node) == "assign":
            instruct = node[1]
            for key, instruction in instruct.items():
                variables[key] = eval(replace_any_var_by_value(instruction, variables))
            next_node = node[2][0]

        path.append(next_node)
        count += 1

    if info_conditions:
        return path, variables, dic_result_cond
    else:
        return path, variables


def type_node(node_value):
    """
    :param node_value: ['if', [[('<=', ["x", 0])]], [2, 3]]
    :return: Type of node ('if', 'assign', ...)
    """
    return node_value[0]


def booleans_condition_on_path(graph, path):
    result = {}
    for node_number in path:
        value_bool = False
        if isinstance(node_number, list):
            # TODO
            print(node_number)
            node_number = node_number[0]
            print(list(node_number))
            # value_bool = bool(node_number[-1])
        if is_boolean_expression_node(graph[node_number]):
            condition = graph[node_number][1]
            result[node_number] = [condition, value_bool]

    return result


def is_boolean_expression_node(node_value):
    if node_value[0] == 'while' or node_value[0] == 'if':
        return True
    else:
        return False


def is_assign_predicate(step):
    # TODO : ! set spaces between all operators in paths
    if ' = ' in step:
        return True
    else:
        return False


def is_bool_predicate(step):
    return not is_assign_predicate(step)


def get_variable_from_assign_predicate(step):
    return step.split(' = ')[0].replace(' ', '')


def get_variable_from_bool_predicate(step):
    comparators = ['==', '<=', '<', '>', '>=', '!=']
    separator = '=='
    step = step.replace('(', '').replace(')', '')
    for comparator in comparators:
        if comparator in step:
            separator = comparator
    # TODO works only on bool value such as x1 == 2 or x1 <= 3!!!!!
    return step.split(separator)[0].replace(' ', '')


def get_next_occurrence_variable(predicate_path, variable):
    for step in predicate_path:
        if variable in step:
            index_var = step.index(variable)
            return step[index_var:index_var + 2]


def clean_path_predicate(predicate_path):
    # ['(x1<=0)', 'x2=0-x1', '(x4==1)'] => ['(x4==1)', 'x2=0-x1', '(x1<=0)']
    # => ['(x2==1)', 'x2=0-x1', '(x1<=0)']
    reversed_predicate_path = list(reversed(predicate_path))
    output = []
    for index, step in enumerate(reversed_predicate_path):
        if is_bool_predicate(step):
            var = get_variable_from_bool_predicate(step)
            value_next = get_next_occurrence_variable(reversed_predicate_path[index + 1:], var[0])
            if value_next is not None:
                # replace its value by next variable that has same first letter
                step = step.replace(var.replace(' ', ''), value_next)
        output.append(step)
    return output


def get_variables_from_predicate(predicate_path):
    variables = []
    for step in predicate_path:
        if is_assign_predicate(step):
            variables.append(get_variable_from_assign_predicate(step))
        elif is_bool_predicate(step):
            variables.append(get_variable_from_bool_predicate(step))
    return variables


def solve_path_predicate(predicate_path):
    """
    :param predicate_path:
    :return:
    """
    problem = Problem()
    # si on a une expression booléenne, il faut donner une relation d'égalité entre la variable isolée
    # et la dernière assignation
    clean_path = clean_path_predicate(predicate_path)
    variables = set(get_variables_from_predicate(clean_path))

    for var in variables:
        problem.addVariable(var, range(-10, 10))

    str_add_cs = 'problem.addConstraint(lambda ' + ','.join(variables) + ':'

    # ['(x2 == 1)', 'x2 = 0-x1', '(x1 <= 0)']
    for step in clean_path:
        if is_assign_predicate(step):
            step = step.replace('=', '==')
        exec(str_add_cs + step + ')')
    return problem.getSolution()


def path_predicate(detailed_steps, graph):
    variables = list(set(get_all_var(graph)))
    order = list(detailed_steps.keys())

    order.sort()

    # voir Cours\IVF\Execsymb\cours6.pdf
    # we do not consider last step (not relevant)
    order.pop()

    result_path_predicate = []

    for step in order:
        if isinstance(detailed_steps[step], dict):
            # assign. For ex: {'x': 'x-1'}
            var = list(detailed_steps[step].keys())[0]
            value = detailed_steps[step][var]
            # process value (eg replace each occurrence of variable 'x' by its value at step 'x8')
            for variable in variables:
                if variable in value:
                    value = value.replace(variable, variable + str(step-1))
            # value_processed = value
            result_path_predicate.append(
                var + str(step) + ' = ' + value
            )
        elif isinstance(detailed_steps[step], list):
            # boolean expression and its  [[[('<=', ["x", 0])]], False]
            bool_expr_str = transform_bool_expr_to_str(detailed_steps[step][0])
            if not detailed_steps[step][1]:
                bool_expr_str = 'not (' + bool_expr_str + ')'

            for variable in variables:
                if variable in bool_expr_str:
                    bool_expr_str = bool_expr_str.replace(variable, variable + str(step))

            result_path_predicate.append(
                bool_expr_str
            )

    return result_path_predicate


def transform_bool_expr_to_str(boolean_expression):
    # [[('<=', ['x', 0]), ('>', ['y', 2])], [('<=', ['x', 0]), ('>', ['y', 2])]]
    # don't know if util
    and_str_list = []
    for and_expr in boolean_expression:
        or_str_list = []
        for or_expr in and_expr:
            or_str = str(or_expr[1][0]) + ' ' + or_expr[0] + ' ' + str(or_expr[1][1])
            or_str_list.append(or_str)
        full_or_str = " or ".join(or_str_list)
        and_str = '(' + full_or_str + ')'
        and_str_list.append(and_str)
    full_and_str = " and ".join(and_str_list)
    return full_and_str


def detailed_steps_path(path, graph):
    result = {}
    for index, step in enumerate(path):
        if type_node(graph[step]) == 'assign':
            result[step] = graph[step][1]
        elif is_boolean_expression_node(graph[step]):
            result[step] = [graph[step][1]]
            if graph[step][-1][0] == path[index - 1]:
                result[step].append(True)
            elif graph[step][-1][1] == path[index - 1]:
                result[step].append(False)
    return result


def path_to_node(node_key, graph):
    path_result = [node_key]
    current_node = node_key

    previous_nodes = get_father_for_node(current_node, graph)
    while previous_nodes:
        choice_to_get_up = [node for node in previous_nodes if node not in path_result][0]
        path_result.append(choice_to_get_up)
        previous_nodes = get_father_for_node(choice_to_get_up, graph)

    return path_result


def old_how_to_get_to_node(node_key, graph):
    path_result = [[node_key]]
    current_node = node_key

    previous_nodes = get_father_for_node(current_node, graph)
    while previous_nodes:
        choice_to_get_up = [node for node in previous_nodes if node not in path_result][0]
        if is_boolean_expression_node(graph[choice_to_get_up]):
            if graph[choice_to_get_up][-1][0] in path_result:
                path_result.append([choice_to_get_up, True])
            elif graph[choice_to_get_up][-1][1] in path_result:
                path_result.append([choice_to_get_up, False])
        else:
            path_result.append([choice_to_get_up])
        previous_nodes = get_father_for_node(choice_to_get_up, graph)

    return path_result


def get_father_for_node(node_key, graph):
    """
    Returns list of nodes that precede given node
    :param node_key:
    :param graph:
    :return:
    """
    result = []
    for key, value in graph.items():
        if node_key in value[-1]:
            result.append(key)

    return result


def process_bool_expression(conditions, variables):
    """
    :param conditions: [[(comp1), (comp2)],[(comp3), (comp4)]], each element is a list of conditions that
    must be respected (and logical gate)
    :param variables:
    :return: evaluated boolean expression
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


def analyze_conditions(bool_expr, variables):
    """
    For each condition in given boolean expression, returns the boolean evaluated.
    The result is returned as a list.
    :param bool_expr:
    :param variables: dic of variables and their values
    :return: list of booleans
    """

    conditions = get_conditions_from_bool_expression(bool_expr)
    result = []
    for comparison in conditions:
        operator = comparison[0]
        values = comparison[1]
        result_comparison = compare(
            operator,
            variables[values[0]] if values[0] in variables else values[0],
            variables[values[1]] if values[1] in variables else values[1],
        )
        result.append(result_comparison)

    return result


def get_conditions_from_bool_expression(boolean_expression):
    """
    :param boolean_expression: simple: [[('<=', ['x', 0])]]
    and: [[('<=', ['x', 0])], [('>', ['y', 2])]]
    or: [[('<=', ['x', 0]), ('>', ['y', 2])]]
    complex: [[('<=', ['x', 0]), ('>', ['y', 2])], [('<=', ['x', 0]), ('>', ['y', 2])]]
    :return: list of conditions (syntax: ('<=', ['x', 0])), without any structure to distinguish between and/or
    """
    conditions = []
    for expressions in boolean_expression:
        for condition in expressions:
            conditions.append(condition)

    return conditions


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


def replace_any_var_by_value(instruction, variables):
    for key, value in variables.items():
        instruction = instruction.replace(key, str(value))
    return instruction


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


def get_following_nodes(node_value):
    return node_value[-1]


def get_children(step_number, graph, visited=None):
    if visited is None:
        visited = []

    children = []
    if step_number == 0:
        return children
    else:
        following_nodes = graph[step_number][-1]

        # we add the list of following nodes
        children.extend(following_nodes)

        # for each following node, we add their following nodes
        # to avoid issue when we encounter potential cycle, we keep track of visited nodes
        for following in [e for e in following_nodes if e not in visited]:
            visited.append(following)
            children.extend(get_children(following, graph, visited))

        return set(children)


def get_accessible_graph(graph, number_node):
    """
    Returns the graph that is accessible starting from a given node
    :param graph:
    :param number_node:
    :return: dictionary
    """
    return {key: graph[key] for key in get_children(number_node, graph) if key != 0}


def get_all_conditions_from_graph(graph):
    """
    :param graph:
    :return: returns a dictionary {node: list(conditions)}
    """
    conditions = {}
    for node, value in graph.items():
        if value[0] == 'if' or value[0] == 'while':
            conditions[node] = get_conditions_from_bool_expression(value[1])

    return conditions


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


def get_utilization_for_variable(graph, variable):
    """
    Returns a list of steps that are utilization (boolean expression or utilization in assignment)
    in a CFG for a given variable
    :param graph:
    :param variable:
    :return: list
    """
    steps = []
    for key, value in graph.items():
        if is_ref(value, variable):
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


def is_def(value_node, variable):
    if value_node[0] != 'assign':
        return False

    if variable in value_node[1]:
        return True
    else:
        return False


def is_ref(value_node, variable):
    if value_node[0] == 'while' or value_node[0] == 'if':
        if variable in get_var_from_bool_expr(value_node[1]):
            return True
        else:
            return False
    elif value_node[0] == 'assign':

        if variable in value_node[1].values():
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


def is_sub_path_in_path(sub_path, path):
    if all(step in path for step in sub_path):
        return True
    else:
        return False