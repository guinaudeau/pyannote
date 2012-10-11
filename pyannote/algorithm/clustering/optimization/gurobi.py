#!/usr/bin/env python
# encoding: utf-8

import sys
import numpy as np
import networkx as nx
import gurobipy as grb
# from progressbar import ProgressBar, Percentage, Bar, ETA

def _n01(g, n1, n2):
    if g.has_edge(n1, n2):
        p = g[n1][n2]['probability']
        if p in [0,1]:
            return int(p)
    return None

def _ij2nn(ij, i2n):
    return i2n[ij[0]], i2n[ij[1]]

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
    # pb = ProgressBar(widgets=[None, ' ', Percentage(), ' ', Bar(),' ', ETA()], 
    #                  term_width=80, poll=1, 
    #                  left_justify=True, fd=sys.stderr)
    
    # create empty model
    model = grb.Model('my Gurobi model')
    
    # model variables
    x = {}
    
    nodes = g.nodes()
    N = len(nodes)
    
    # one variable per pair of nodes
    # pb.widgets[0] = 'Variables'
    
    # Σi|1..N ( Σj|i+1..N 1 )
    # pb.maxval = int(N*(N-1)/2.)
    # pb.start()
    for i1 in range(N):
        # Σi|1..i1 ( Σj|i+1..N 1 )
        # n = int(N*i1 - i1**2/2. - i1/2.)
        # pb.update(n)
        n1 = nodes[i1]
        for i2 in range(i1+1, N):
            n2 = nodes[i2]
            x[n1, n2] = model.addVar(vtype=grb.GRB.BINARY)
    
    # pb.finish()
    
    model.update()
    
    # transitivity constraints
    # pb.widgets[0] = 'Constraints'
    
    # Σi|1..N ( Σj|i+1..N ( Σk|j+1..N 1 ) ) 
    # pb.maxval = int(N**3/6. - N**2/2. + N/3.)
    # pb.start()
    
    p = {}
    i2n = {}
    for i1 in range(N):
        
        # Σi|1..i1 ( Σj|i+1..N ( Σk|j+1..N 1 ) ) 
        # n = int(N**2*i1/2.- N*i1/2.-N*(i1**2/2.+i1/2.)+i1**3/6.+i1**2/2.+i1/3.)
        # pb.update(n)
        
        n1 = nodes[i1]
        i2n[1] = n1
        
        for i2 in range(i1+1, N):
            
            n2 = nodes[i2]
            i2n[2] = n2
            
            # probability n1 <--> n2
            p[1,2] = _n01(g, n1, n2)
            
            if p[1,2] in [0, 1]:
                model.addConstr(x[n1, n2] == p[1,2])
            
            for i3 in range(i2+1, N):
                
                n3 = nodes[i3]
                i2n[3] = n3
                
                # probability n1 <--> n3
                p[1,3] = _n01(g, n1, n3)
                
                # probability n2 <--> n3
                p[2,3] = _n01(g, n2, n3)
                
                # set of values taken by the 3 edges
                # {0}, {1}, {None}, {0, 1}, {0, None}, {1, None} or {0, 1, None}
                values_set = set(p.values())
                
                if not (values_set - set([0, 1])):
                    # there are only 0s and 1s
                    # those constraints will be taken care of by the outer loop
                    continue
                
                # {0: number of 0s, 1: number of 1s, None: number of Nones}
                value2count = {v: p.values().count(v) for v in [0, 1, None]}
                value2list = {v: [ij for ij in p if p[ij] == v] 
                              for v in [0, 1, None]}
                
                # 0/1 values
                values_set = values_set - set([None])
                num_values = len(values_set)
                
                # there is only one None
                if value2count[None] == 1:
                    
                    ij_none = value2list[None][0]
                    ninj_none = _ij2nn(ij_none, i2n)
                    if num_values == 1:
                        # there are one None and two 0s (or two 1s)
                        # set the one None to 0 (or to 1)
                        model.addConstr(x[ninj_none] == values_set.pop())
                    else:
                        # there are one None, one 0 and one 1
                        # set the one None to 0
                        model.addConstr(x[ninj_none] == 0)
                
                # there are two Nones
                elif value2count[None] == 2:
                    
                    ij = value2list[None][0]
                    ninj = _ij2nn(ij, i2n)
                    jk = value2list[None][1]
                    njnk = _ij2nn(jk, i2n)
                    
                    if value2count[1] == 1:
                        # there are two Nones and one 1
                        # set the two Nones equal to each other
                        model.addConstr(x[ninj] == x[njnk])
                    else:
                        # there two Nones and one 0
                        # set the two Nones different from each other
                        model.addConstr(x[ninj] + x[njnk] <= 1)
                
                else:
                    model.addConstr(x[n2, n3] + x[n1, n3] - x[n1, n2] <= 1)
                    model.addConstr(x[n1, n2] + x[n1, n3] - x[n2, n3] <= 1)
                    model.addConstr(x[n1, n2] + x[n2, n3] - x[n1, n3] <= 1)
                
    
    # pb.finish()
    
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
    for (n1, n2), var in x.iteritems():
        g.add_node(n1)
        g.add_node(n2)
        if var.x == 1.:
            g.add_edge(n1, n2)
    return g

