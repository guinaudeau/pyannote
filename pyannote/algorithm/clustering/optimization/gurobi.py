#!/usr/bin/env python
# encoding: utf-8

import gurobipy as grb
import numpy as np
import networkx as nx
import pyfusion.normalization.bayes

def new_clustering_model(N, problem_name=None):
    """
    Create and return Gurobi clustering model
    
    The model contains the following variables and constraints:
        * NxN binary variables x[i,j] indicating whether items i and j
          are in the same cluster (denoted i-j, the opposite being i|j)
        * NxN symmetry constraints
                     i-j ==> j-i
                     i|j ==> j|i
        * NxNxN transitity constraints
                     i-j and j-k ==> i-k
                     i-j and j|k ==> i|k
    
    Note that returned Gurobi model has no set objective.
    
    Parameters
    ----------
    N : int
        Size of the model (number of clustered items).
    name : str, optional
        Name of the model
    
    Returns
    -------
    model : :class:`gurobipy.Model`
        Gurobi clustering model with no objective.
    x : dict
        Gurobi clustering variable x[i,j]
    """
    
    # create empty model
    model = grb.Model(problem_name)
    
    # add (to-be-optimized) variables
    # xij = 1 means i-j (i & j in the same cluster)
    x = {}
    for i in range(N):
        for j in range(N):
            name = "x_%d_%d" % (i,j)
            x[i, j] = model.addVar(vtype=grb.GRB.BINARY, name=name)
    
    # update model with new (to-be-optimized) variables
    model.update()
    
    # add symmetry constraint
    # i-j ==> j-i
    s = {}
    for i in range(N):
        for j in range(N):
            s[i,j] = (x[i,j] == x[j,i])
            name = "s_%d_%d" % (i,j)
            model.addConstr(s[i,j], name)
    
    # add transitivity constraints
    # i-j and j-k ==> i-k
    # (also implies i-j and j|k ==> i|k)
    t = {}
    for i in range(N):
        for j in range(N):
            for k in range(N):
                t[i,j,k] = (1-x[i,j])+(1-x[j,k]) >= (1-x[i,k])
                name = "t_%d_%d_%d" % (i, j, k)
                model.addConstr(t[i,j,k], name)
    
    # return the model & its variables
    return model, x


def optimize(N, model, x):
    """
    Optimize model and return clusters
    
    Parameters
    ----------
    N : int
        Size of the model (number of clustered items).
    model : :class:`gurobipy.Model`
        Gurobi clustering model
    x : dict
        Gurobi clustering variable x[i,j]
    
    Returns
    -------
    clusters : list of lists
    
    """
    
    model.optimize()
    
    # read results as a graph
    # one node per label, edges between same-cluster labels
    g = nx.Graph()
    for i in range(N):
        g.add_node(i)
        for j in range(N):
            if j <= i:
                continue
            value = x[i,j].x
            if value:
                g.add_edge(i, j)
        
    # find clusters (connected components in graph)
    clusters = nx.connected_components(g)
    
    return clusters


def graph2gurobi(g):
    
    # create empty model
    model = grb.Model('my Gurobi model')
    
    # model variables
    x = {}
    
    for node, other_node, data in g.edges_iter(data=True):
        
        probability = data['probability']
        
        # one variable per pair of nodes
        x[node, other_node] = model.addVar(vtype=grb.GRB.BINARY)
        x[other_node, node] = model.addVar(vtype=grb.GRB.BINARY)
        
        # symmetry constraints
        model.addConstr(x[node, other_node] == x[other_node, node])
        
        # 0/1 probability constraints
        if probability == 1:
            # these 2 nodes must be in the same cluster
            model.addConstr(x[node, other_node] == 1)
        elif probability == 0:
            # these 2 nodes must be in 2 different clusters
            model.addConstr(x[node, other_node] == 0)
    
    # transitivity constraints
    for n1 in g:
        for n2 in g:
            for n3 in g:
                model.addConstr((1-x[n1, n2])+(1-x[n2, n3]) >= (1-x[n1, n3]))
    
    # update model
    model.update()
    
    # return the model & its variables
    return model, x
    
    
    
