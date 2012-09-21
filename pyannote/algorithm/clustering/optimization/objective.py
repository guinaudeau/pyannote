#!/usr/bin/env python
# encoding: utf-8

import gurobipy as grb
import numpy as np
import networkx as nx

# class BaseObjectiveMixin(object):
#     
#     def omx_setup(self, **kwargs):
#         pass
#         
#     def omx_objective(self, **kwargs):
#         pass
# 
# class FinkelOMx(BaseObjectiveMixin):
#     """
#     Maximize ∑ α.xij.log pij + (1-α).(1-xij).log (1-pij)
#             j>i
#     """
#     def omx_setup(self, alpha=None, **kwargs):
#         """
#         Set-up objective parameters
#         
#         Parameters
#         ----------
#         alpha : float
#             Value of α in above formula
#         
#         """
#         self.omx_alpha = alpha
#     
#     def omx_objective(self, x=None, P=None):
#         """
#         Get following objective:
#         Maximize ∑ α.xij.log pij + (1-α).(1-xij).log (1-pij)
#                 j>i
#         
#         Parameters
#         ----------
#         x : dict
#             Gurobi clustering variable x[i,j]
#         P : array-like (N, N)
#             pij in above formula.
#             It is the probability that i and j are in the same cluster
#             Assume that P is a symmetric matrix with values in range [0, 1].
#         
#         Returns
#         -------
#         objective :
#             Gurobi objective
#         direction : {grb.GRB.MAXIMIZE, grb.GRB.MINIMIZE}
#              Optimization direction (maximize or minimize objective)
#         """
#         N,N = P.shape
#         
#         h1 = np.maximum(-1e10, np.log(P))
#         h0 = np.maximum(-1e10, np.log(1 - P))
#         
#         objective = grb.quicksum([self.omx_alpha*h1[i,j]*x[i,j]+
#                                   (1-self.omx_alpha)*h0[i,j]*(1-x[i,j])
#                                   for i in range(N) for j in range(i+1, N)])
#         
#         return objective, grb.GRB.MAXIMIZE


def obj_IOlogP(x, P, alpha):
    """
    Get following objective:
    Maximize ∑ α.xij.log pij + (1-α).(1-xij).log (1-pij)
            j>i
    
    Parameters
    ----------
    x : dict
        Gurobi clustering variable x[i,j]
    P : array-like (N, N)
        pij in above formula.
        It is the probability that i and j are in the same cluster
        Assume that P is a symmetric matrix with values in range [0, 1].
    alpha : float
        Value of α in above formula
    
    Returns
    -------
    objective :
        Gurobi objective
    direction : {grb.GRB.MAXIMIZE, grb.GRB.MINIMIZE}
         Optimization direction (maximize or minimize objective)
    """
    
    N,N = P.shape
    
    h1 = np.maximum(-1e10, np.log(P))
    h0 = np.maximum(-1e10, np.log(1 - P))
    
    objective = grb.quicksum([alpha*h1[i,j]*x[i,j]+
                              (1-alpha)*h0[i,j]*(1-x[i,j])
                              for i in range(N) for j in range(i+1, N)])
    
    return objective, grb.GRB.MAXIMIZE


def obj_IOP(x, P, alpha):
    """
    Get following objective:
    Maximize ∑ α.xij.pij + (1-α).(1-xij).(1-pij)
            j>i
    
    Parameters
    ----------
    x : dict
        Gurobi clustering variable x[i,j]
    P : array-like (N, N)
        pij in above formula.
        It is the probability that i and j are in the same cluster
        Assume that P is a symmetric matrix with values in range [0, 1].
    alpha : float
        Value of α in above formula
    
    Returns
    -------
    objective :
        Gurobi objective
    direction : {grb.GRB.MAXIMIZE, grb.GRB.MINIMIZE}
         Optimization direction (maximize or minimize objective)
    
    """
    
    N,N = P.shape
    
    objective = grb.quicksum([alpha*P[i,j]*x[i,j]+
                              (1-alpha)*(1-P[i,j])*(1-x[i,j])
                              for i in range(N) for j in range(i+1, N)])
    return objective, grb.GRB.MAXIMIZE

# def obj_Q(x, P):
#     """
#     Maximize modularity
#     
#     Parameters
#     ----------
#     x : dict
#         Gurobi clustering variable x[i,j]
#     P : array-like (N, N)
#         pij is the probability that i and j are in the same cluster
#     
#     Returns
#     -------
#     objective :
#         Gurobi objective
#     direction : {grb.GRB.MAXIMIZE, grb.GRB.MINIMIZE}
#          Optimization direction (maximize or minimize objective)
#     
#     """
#     
#     N,N = P.shape
#     
#     # total weights in graph
#     m = np.sum(P)
#     
#     # node degree (total weight of {in|out}going edges)
#     kin = np.sum(P, axis=0)[:, np.newaxis]
#     kout = np.sum(P, axis=1)[:, np.newaxis]
#         
#     # modularity matrix
#     Q = (P - kout*kin.T/m) / m
#     
#     objective = grb.quicksum([Q[i,j] * x[i,j] 
#                               for i in range(N) for j in range(N)])
#     
#     return objective, grb.GRB.MAXIMIZE


def obj_bigcluster(x, g):
    
    nodes = g.nodes()
    objective = grb.quicksum([x[node, other_node] 
                              for node in nodes for other_node in nodes])
    return objective, grb.GRB.MAXIMIZE

def obj_smallcluster(x, g):

    nodes = g.nodes()
    objective = grb.quicksum([x[node, other_node] 
                              for node in nodes for other_node in nodes])
    return objective, grb.GRB.MINIMIZE

def obj_Q(x, g):
    """
    Maximize modularity
    
    Parameters
    ----------
    x : dict
        Gurobi clustering variable x[i,j]
    g : nx.Graph
        
    
    Returns
    -------
    objective :
        Gurobi objective
    direction : {grb.GRB.MAXIMIZE, grb.GRB.MINIMIZE}
         Optimization direction (maximize or minimize objective)
    
    """
    
    nodes = g.nodes()
    N = len(nodes)
    
    P = np.array(nx.to_numpy_matrix(g, nodelist=nodes, weight='probability'))
    
    # total weights in graph
    m = np.sum(P)
    
    # node degree (total weight of {in|out}going edges)
    kin = np.sum(P, axis=0)[:, np.newaxis]
    kout = np.sum(P, axis=1)[:, np.newaxis]
        
    # modularity matrix
    Q = (P - kout*kin.T/m) / m
    
    objective = grb.quicksum([Q[n,m] * x[node, other_node] 
                              for n, node in enumerate(nodes) 
                              for m, other_node in enumerate(nodes)
                              if m > n and Q[n,m] > 0])
    
    # objective = grb.quicksum([Q[i,j] * x[i,j] 
    #                           for i in range(N) for j in range(N)])
    
    return objective, grb.GRB.MAXIMIZE
