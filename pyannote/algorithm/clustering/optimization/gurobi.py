#!/usr/bin/env python
# encoding: utf-8

import sys
import numpy as np
import networkx as nx
import gurobipy as grb
from progressbar import ProgressBar, Percentage, Bar, ETA

# import pyfusion.normalization.bayes

# def new_clustering_model(N, problem_name=None):
#     """
#     Create and return Gurobi clustering model
#     
#     The model contains the following variables and constraints:
#         * NxN binary variables x[i,j] indicating whether items i and j
#           are in the same cluster (denoted i-j, the opposite being i|j)
#         * NxN symmetry constraints
#                      i-j ==> j-i
#                      i|j ==> j|i
#         * NxNxN transitity constraints
#                      i-j and j-k ==> i-k
#                      i-j and j|k ==> i|k
#     
#     Note that returned Gurobi model has no set objective.
#     
#     Parameters
#     ----------
#     N : int
#         Size of the model (number of clustered items).
#     name : str, optional
#         Name of the model
#     
#     Returns
#     -------
#     model : :class:`gurobipy.Model`
#         Gurobi clustering model with no objective.
#     x : dict
#         Gurobi clustering variable x[i,j]
#     """
#     
#     # create empty model
#     model = grb.Model(problem_name)
#     
#     # add (to-be-optimized) variables
#     # xij = 1 means i-j (i & j in the same cluster)
#     x = {}
#     for i in range(N):
#         for j in range(N):
#             name = "x_%d_%d" % (i,j)
#             x[i, j] = model.addVar(vtype=grb.GRB.BINARY, name=name)
#     
#     # update model with new (to-be-optimized) variables
#     model.update()
#     
#     # add symmetry constraint
#     # i-j ==> j-i
#     s = {}
#     for i in range(N):
#         for j in range(N):
#             s[i,j] = (x[i,j] == x[j,i])
#             name = "s_%d_%d" % (i,j)
#             model.addConstr(s[i,j], name)
#     
#     # add transitivity constraints
#     # i-j and j-k ==> i-k
#     # (also implies i-j and j|k ==> i|k)
#     t = {}
#     for i in range(N):
#         for j in range(N):
#             for k in range(N):
#                 t[i,j,k] = (1-x[i,j])+(1-x[j,k]) >= (1-x[i,k])
#                 name = "t_%d_%d_%d" % (i, j, k)
#                 model.addConstr(t[i,j,k], name)
#     
#     # return the model & its variables
#     return model, x


# def optimize(N, model, x):
#     """
#     Optimize model and return clusters
#     
#     Parameters
#     ----------
#     N : int
#         Size of the model (number of clustered items).
#     model : :class:`gurobipy.Model`
#         Gurobi clustering model
#     x : dict
#         Gurobi clustering variable x[i,j]
#     
#     Returns
#     -------
#     clusters : list of lists
#     
#     """
#     
#     model.optimize()
#     
#     # read results as a graph
#     # one node per label, edges between same-cluster labels
#     g = nx.Graph()
#     for i in range(N):
#         g.add_node(i)
#         for j in range(N):
#             if j <= i:
#                 continue
#             value = x[i,j].x
#             if value:
#                 g.add_edge(i, j)
#         
#     # find clusters (connected components in graph)
#     clusters = nx.connected_components(g)
#     
#     return clusters


def graph2gurobi(g):
    """
    Create Gurobi clustering model from graph
    
    Parameters
    ----------
    g : nx.Graph
        One node per track. Edge attribute 'probability' between nodes.
        
    Returns
    -------
    model : gurobipy.grb.Model
        Gurobi clustering model
    x : dict
        Dictionary of gurobi.grb.Var
        x[node, other_node] is a boolean variable indicating whether
        node and other_node are in the same cluster
    
    """
    pb = ProgressBar(widgets=[None, ' ', Percentage(), ' ', Bar(),' ', ETA()], 
                     term_width=80, poll=1, 
                     left_justify=True, fd=sys.stderr)
    
    # create empty model
    model = grb.Model('my Gurobi model')
    
    # model variables
    x = {}
    
    nodes = g.nodes()
    N = len(nodes)
    
    # one variable per pair of nodes
    pb.widgets[0] = 'Variables'
    pb.maxval = N
    pb.start()
    for n, node in enumerate(nodes):
        pb.update(n+1)
        for other_node in nodes:
            x[node, other_node] = model.addVar(vtype=grb.GRB.BINARY)
    pb.finish()
    
    model.update()
    
    # symmetry constraints
    pb.widgets[0] = 'Symmetry constraints'
    pb.maxval = N
    pb.start()
    for n, node in enumerate(nodes):
        pb.update(n+1)
        for other_node in nodes:
            model.addConstr(x[node, other_node] == x[other_node, node])
    pb.finish()
    
    # trivial (0/1) probability constraints
    pb.widgets[0] = 'Hard constraints'
    edges = [(e, f, d) for (e, f, d) in g.edges(data=True) 
                       if d['probability'] in [0, 1]]
    pb.maxval = len(edges)
    pb.start()
    for n, (node, other_node, data) in enumerate(edges):
        pb.update(n+1)
        
        probability = data['probability']
        
        if probability == 1:
            # these 2 nodes must be in the same cluster
            model.addConstr(x[node, other_node] == 1)
        
        elif probability == 0:
            # these 2 nodes must be in 2 different clusters
            model.addConstr(x[node, other_node] == 0)
    
    pb.finish()
    
    # transitivity constraints
    pb.widgets[0] = 'Transitivity constraints'
    pb.maxval = N
    pb.start()
    for i1 in range(N):
        pb.update(i1+1)
        n1 = nodes[i1]
        for i2 in range(i1+1, N):
            n2 = nodes[i2]
            for i3 in range(i2+1, N):
                n3 = nodes[i3]
                model.addConstr(x[n2, n3] + x[n1, n3] - x[n1, n2] <= 1)
                model.addConstr(x[n1, n2] + x[n1, n3] - x[n2, n3] <= 1)
                model.addConstr(x[n1, n2] + x[n2, n3] - x[n1, n3] <= 1)
    
    pb.finish()
    
    # return the model & its variables
    return model, x
    
def gurobi2graph(model, x):
    """
    Generate graph from optimized Gurobi model
    
    Parameters
    ----------
    model : gurobipy.grp.Model
        Optimized Gurobi model
    x : dict
        Dictionary of Gurobi variables
        x[node, other_node] value equals 1 if node and other_node are in the
        same cluster
        
    Returns
    -------
    g : nx.Graph
        Sparsely connected graph with edges between nodes that are in the
        same cluster
    
    """
    g = nx.Graph()
    
    for (node, other_node), var in x.iteritems():
        g.add_node(node)
        g.add_node(other_node)
        if var.x == 1.:
            g.add_edge(node, other_node)
    
    return g

