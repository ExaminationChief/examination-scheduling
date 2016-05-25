#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
paths = os.getcwd().split('/')
path = ''
for p in paths:
    path += '%s/' % p
    if p == 'examination-scheduling':
        break
sys.path.append(path)

import logging
from gurobipy import Model


def convert_to_table(variables, *dim):
    """ @param variables: dictionnary of variables
        @param dim: dimension of variables
        convert it to a string that represent a tabel
    """
    res = '     |  %s\n' % '  |  '.join([str(i) for i in range(dim[0])])
    res += '%s\n' % '|'.join(['-----' for i in range(dim[0] + 1)])
    if len(dim) > 1:
        for j in range(dim[1]):
            res += '  %s  |  %s\n' % (j, '  |  '.join([str(int(variables[i, j].X)) for i in range(dim[0])]))
            res += '%s\n' % '|'.join(['-----' for i in range(dim[0] + 1)])
    else:
        res += '  1  |  %s\n' % '  |  '.join([str(int(variables[i].X)) for i in range(dim[0])])
        res += '%s\n' % '|'.join(['-----' for i in range(dim[0] + 1)])
    return res


def get_dimensions_from(x, y):
    """ @param variables: variable from gurobi
        return the maximal number or each rank in the tuple key
    """
    n, r, p = set(), set(), set()
    for key, _ in x.iteritems():
        n.add(key[0])
        r.add(key[1])
    for key, _ in y.iteritems():
        n.add(key[0])
        p.add(key[1])
    return len(n), len(r), len(p)


def get_value(var):
        """ Return the value of var if possible, else 0
        """
        try:
            return var.X
        except Exception as e:
            logging.warning(str(e))
            return 0.0


def update_variable(problem, **dimensions):
    """ @param problem: either a problem inheriting from BaseProblem class or a guroby problem
        Transform the variable of the given problem to the two following variables:
                    x[i, k]: 1 if exam i is taking place in room k
                    y[i, l]: 1 if exam i happens during period l
        @returns: x, y
    """
    # problem from Base_problem class
    n = dimensions.get('n', 0)
    r = dimensions.get('r', 0)
    p = dimensions.get('p', 0)
    try:
        if problem.__class__.__name__.endswith('Problem'):
            return problem.update_variable()
        elif issubclass(problem.__class__, Model):
            try:
                try:
                    x = {(i, k): 1.0 if sum([problem.getVarByName("x_%s_%s_%s" % (i, k, l)).X > 0 for l in range(p)]) else 0.0
                         for i in range(n) for k in range(r)}
                except:
                    x = {(i, k): problem.getVarByName("x_%s_%s" % (i, k)) for i in range(n) for k in range(r)}
                y = {(i, l): problem.getVarByName("y_%s_%s" % (i, l)).X for i in range(n) for l in range(p)}
            except:
                logging.warning("update_variable: problem %s has not been solved" % problem.ModelName)
                x = {(i, k): 0.0 for i in range(n) for k in range(r)}
                y = {(i, l): 0.0 for i in range(n) for l in range(p)}
            return x, y
    except:
        logging.exception("update_variable: impossible to update the variable of the given problem %s"
                          % problem.ModelName)
    return ({}, {})
