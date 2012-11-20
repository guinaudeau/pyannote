#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012 Herve BREDIN (bredin@limsi.fr)

# This file is part of PyAnnote.
# 
#     PyAnnote is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     PyAnnote is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with PyAnnote.  If not, see <http://www.gnu.org/licenses/>.

import os
import socket
os.putenv('GRB_LICENSE_FILE', 
          "%s/licenses/%s.lic" % (os.getenv('GUROBI_HOME'),
                                  socket.gethostname()))
import gurobipy as grb

import sys
import numpy as np
import networkx as nx
from graph import LabelNode, IdentityNode
from pyannote.base.annotation import Unknown

optimization_status = {
    grb.GRB.LOADED: 'Model is loaded, but no solution information is '
                    'available.',
    grb.GRB.OPTIMAL: 'Model was solved to optimality (subject to tolerances), '
                     'and an optimal solution is available.',
    grb.GRB.INFEASIBLE: 'Model was proven to be infeasible.',
    grb.GRB.INF_OR_UNBD: 'Model was proven to be either infeasible or '
                         'unbounded.',
    grb.GRB.UNBOUNDED: 'Model was proven to be unbounded.',
    grb.GRB.CUTOFF: 'Optimal objective for model was proven to be worse than '
                    'the value specified in the Cutoff parameter. No solution '
                    'information is available.',
    grb.GRB.ITERATION_LIMIT: 'Optimization terminated because the total number '
                             'of simplex iterations performed exceeded the '
                             'value specified in the IterationLimit parameter, '
                             'or because the total number of barrier '
                             'iterations exceeded the value specified in the '
                             'BarIterLimit parameter.',
    grb.GRB.NODE_LIMIT: 'Optimization terminated because the total number of '
                        'branch-and-cut nodes explored exceeded the value '
                        'specified in the NodeLimit parameter.',
    grb.GRB.TIME_LIMIT: 'Optimization terminated because the time expended '
                        'exceeded the value specified in the TimeLimit '
                        'parameter.',
    grb.GRB.SOLUTION_LIMIT: 'Optimization terminated because the number of '
                            'solutions found reached the value specified in '
                            'the SolutionLimit parameter.',
    grb.GRB.INTERRUPTED: 'Optimization was terminated by the user.',
    grb.GRB.NUMERIC: 'Optimization was terminated due to unrecoverable '
                     'numerical difficulties.',
    grb.GRB.SUBOPTIMAL: 'Unable to satisfy optimality tolerances; '
                        'a sub-optimal solution is available.'
}


# from progressbar import ProgressBar, Percentage, Bar, ETA

def _n01(g, n1, n2):
    if g.has_edge(n1, n2):
        p = g[n1][n2]['probability']
        if p in [0,1]:
            return int(p)
    return None

def _ij2nn(ij, i2n):
    return i2n[ij[0]], i2n[ij[1]]

class GurobiModel(object):
    """
    
    """
    def __init__(self, G, method=-1, mipGap=1e-4, timeLimit=None, 
                         threads=None, quiet=True):
        super(GurobiModel, self).__init__()
        self.graph = G
        self.method = method
        self.mipGap = mipGap
        self.timeLimit = timeLimit
        self.threads = threads
        self.quiet = quiet
        self.model, self.x = self.__model(G)
        
    def __model(self, G):
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
        
        # make sure graph only contains LabelNode(s) and IdentityNode(s)
        bad_nodes = [node for node in G.nodes_iter() 
                          if not isinstance(node, (LabelNode, IdentityNode))]
        if len(bad_nodes) > 0:
            raise ValueError('Graph contains nodes other than'
                             'LabelNode or IdentityNode.')
    
        # pb = ProgressBar(widgets=[None, ' ', Percentage(), ' ', Bar(),' ', ETA()], 
        #                  term_width=80, poll=1, 
        #                  left_justify=True, fd=sys.stderr)
    
        # create empty model & dictionary to store its variables
        model = grb.Model('My model')
        model.setParam('OutputFlag', False)
        
        x = {}
    
        nodes = G.nodes()
        N = len(nodes)
        
        # one variable per node pair
        for i1 in range(N):
            n1 = nodes[i1]
            for i2 in range(i1+1, N):
                n2 = nodes[i2]
                x[n1, n2] = model.addVar(vtype=grb.GRB.BINARY)
        
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
                p[1,2] = _n01(G, n1, n2)
            
                if p[1,2] in [0, 1]:
                    model.addConstr(x[n1, n2] == p[1,2])
            
                for i3 in range(i2+1, N):
                
                    n3 = nodes[i3]
                    i2n[3] = n3
                
                    # probability n1 <--> n3
                    p[1,3] = _n01(G, n1, n3)
                
                    # probability n2 <--> n3
                    p[2,3] = _n01(G, n2, n3)
                
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
        
        model.setParam(grb.GRB.Param.Method, self.method)
        
        
        # -- Parameters to reduce memory consumption
        
        if self.threads is not None:
            # Controls the number of threads to apply to parallel MIP.
            model.setParam(grb.GRB.Param.Threads, self.threads)
        
        # When the amount of memory used to store nodes (measured in GBytes)
        # exceeds the specified parameter value, nodes are written to disk
        model.setParam(grb.GRB.Param.NodefileStart, 0.5)
        
        # -- Parameters to prevent optimization from lasting forever
        
        # The MIP solver will terminate (with an optimal result) when the
        # relative gap between the lower and upper objective bound is less than 
        # MIPGap times the upper bound.
        model.setParam(grb.GRB.Param.MIPGap, self.mipGap)
        
        if self.timeLimit is not None:
            # Limits the total time expended (in seconds).
            model.setParam(grb.GRB.Param.TimeLimit, self.timeLimit)
        
        # The MIPFocus parameter allows you to modify your high-level solution strategy, depending on your goals. By default, the Gurobi MIP solver strikes a balance between finding new feasible solutions and proving that the current solution is optimal. If you are more interested in finding feasible solutions quickly, you can select MIPFocus=1. If you believe the solver is having no trouble finding good quality solutions, and wish to focus more attention on proving optimality, select MIPFocus=2. If the best objective bound is moving very slowly (or not at all), you may want to try MIPFocus=3 to focus on the bound.
        # model.setParam(grb.GRB.Param.MIPFocus, 1)
        
        # Enables or disables solver output.
        model.setParam(grb.GRB.Param.OutputFlag, not self.quiet)
        
        # return the model & its variables
        return model, x
    
    
    def objective_Finkel(self, alpha=0.5, log_prob=False):
        """
        Maximize ∑  α.xij.pij + (1-α).(1-xij).(1-pij)
                j>i
        
        Parameters
        ----------
        alpha : float, optional
            Value of α in above formulas (default value is 0.5).
        log_prob : bool, optional
            If True, use log pij and log (1-pij) in place of pij and (1-pij)
        
        """
        
        nodes = self.graph.nodes()
        P = np.array(nx.to_numpy_matrix(self.graph,
                                        nodelist=nodes,
                                        weight='probability'))
        
        # normalization coefficient
        k = 1000. / np.sum([1 for n,_ in enumerate(nodes)
                              for m,_ in enumerate(nodes)
                              if m > n and P[n,m] not in [0, 1]])
        
        a = alpha
        if log_prob:
            objective = k * grb.quicksum([a*np.log(P[n,m])*self.x[N,M] +
                                         (1-a)*np.log(1-P[n,m])*(1-self.x[N,M])
                                          for n, N in enumerate(nodes)
                                          for m, M in enumerate(nodes)
                                          if m > n and P[n,m] not in [0, 1]])
        else:
            objective = k * grb.quicksum([a*P[n,m]*self.x[N,M] +
                                          (1-a)*(1-P[n,m])*(1-self.x[N,M])
                                          for n, N in enumerate(nodes)
                                          for m, M in enumerate(nodes)
                                          if m > n and P[n,m] not in [0, 1]])
        
        return objective, grb.GRB.MAXIMIZE
    
    def setObjective(self, type='finkel', alpha=0.5, log_prob=False):
        """
        Set the objective function
        
        Parameters
        ----------
        type : {'finkel'}
            finkel: Maximize ∑  α.xij.pij + (1-α).(1-xij).(1-pij)
                            j>i
        alpha : float, optional
            Value of α in above formulas (default value is 0.5).
        log_prob : bool, optional
            If True, use log pij and log (1-pij) in place of pij and (1-pij)
        """
        
        if type == 'finkel':
            o, d = self.objective_Finkel(alpha=alpha,
                                         log_prob=log_prob)
        
        self.model.setObjective(o, d)
    
    def optimize(self):
        self.model.optimize()
    
    def get_status(self):
        status = self.model.getAttr(grb.GRB.Attr.Status)
        return status, optimization_status[status]
    
    def reconstruct(self, annotation):
        """
        Generate new annotation from optimized Gurobi model
        
        Parameters
        ----------
        annotation : Annotation
            Original annotation
    
        Returns
        -------
        new_annotation : dictionary of Annotation
    
        """
        
        g = nx.Graph()
        for (n1, n2), var in self.x.iteritems():
            g.add_node(n1)
            g.add_node(n2)
            if var.x == 1.:
                g.add_edge(n1, n2)
        
        uri = annotation.video
        modality = annotation.modality
        
        translation = {}
        for cc in nx.connected_components(g):
        
            labelNodes = [node for node in cc 
                               if isinstance(node, LabelNode) 
                              and node.uri == uri 
                              and node.modality == modality]
            
            identityNodes = [node for node in cc 
                                  if isinstance(node, IdentityNode)]
            
            if len(identityNodes) > 1:
                raise ValueError('Looks like there are more than one identity '
                                 'in this cluster: %s' % [node.identifier 
                                                    for node in identityNodes])
            elif len(identityNodes) == 1:
                identifier = identityNodes[0].identifier
            else:
                identifier = Unknown()
            
            for node in labelNodes:
                translation[node.label] = identifier
        
        return (annotation % translation).smooth()
        