#!/usr/bin/env python
# encoding: utf-8

import os
import socket
os.putenv('GRB_LICENSE_FILE', 
          "%s/licenses/%s.lic" % (os.getenv('GUROBI_HOME'),
                                  socket.gethostname()))

import gurobipy as grb
from graph import PROBABILITY
from pyannote.base.annotation import Annotation, Unknown
from node import IdentityNode, TrackNode
import networkx as nx
import numpy as np

class PCenterModel(object):
    
    def __init__(self, graph, alpha=0.5, method=-1, mipGap=1e-4, timeLimit=None,
                       threads=None, quiet=True, missing_constraint=False):
        
        super(PCenterModel, self).__init__()
        self.graph = graph
        self.alpha = alpha
        self.missing_constraint = missing_constraint
        self.method = method
        self.mipGap = mipGap
        self.timeLimit = timeLimit
        self.threads = threads
        self.quiet = quiet
        self.model, self.x = self._model(graph)
    
    def _model(self, G):
        
        model = grb.Model()
        model.setParam('OutputFlag', False)
        
        nodes = G.nodes()
        
        # Equation 1.2 (in Dupuy et al., JEP'12)
        x = {}
        for k, nk in enumerate(nodes):
            for j, nj in enumerate(nodes):
                x[nk,nj] = model.addVar(vtype=grb.GRB.BINARY)
        model.update()
        
        # Equation 1.3 (in Dupuy et al., JEP'12)
        for j,nj in enumerate(nodes):
            model.addConstr(grb.quicksum([x[nk,nj] for k,nk in enumerate(nodes)]) == 1)
        
        # Equation 1.4 (in Dupuy et al., JEP'12)
        for k,nk in enumerate(nodes):
            for j,nj in enumerate(nodes):
                if nk == nj:
                    continue
                model.addConstr((1-G[nk][nj][PROBABILITY])*x[nk,nj] <= self.alpha)
        
        if not self.missing_constraint: 
            # Missing Equation 1.5
            for k,nk in enumerate(nodes):
                for j,nj in enumerate(nodes):
                    model.addConstr(x[nk,nk] >= x[nk,nj])
        
        # Equation 1 (in Dupuy et al., JEP'12)
        nClusters = grb.quicksum([x[nk,nk] for k,nk in enumerate(nodes)])
        dispersion = grb.quicksum([(1-G[nk][nj][PROBABILITY])*x[nk,nj] 
                                   for k,nk in enumerate(nodes) 
                                   for j,nj in enumerate(nodes)
                                   if nj != nk])
        model.setObjective(nClusters + dispersion, grb.GRB.MINIMIZE)

        model.setParam(grb.GRB.Param.Method, self.method)
        if self.threads is not None:
            model.setParam(grb.GRB.Param.Threads, self.threads)
        model.setParam(grb.GRB.Param.NodefileStart, 0.5)
        model.setParam(grb.GRB.Param.MIPGap, self.mipGap)
        if self.timeLimit is not None:
            model.setParam(grb.GRB.Param.TimeLimit, self.timeLimit)
        model.setParam(grb.GRB.Param.OutputFlag, not self.quiet)
        
        return model, x
    
    def optimize(self):
        self.model.optimize()
        return self.getAnnotations()
    
    def getAnnotations(self):
        
        c = nx.Graph()
        for (nk,nj), var in self.x.iteritems():
            c.add_node(nk)
            c.add_node(nj)
            # node j is assigned to center node k
            if var.x == 1:
                c.add_edge(nk,nj)
                # node k is a center
                if nk == nj:
                    c.node[nk]['center'] = True
        clusters = nx.connected_components(c)
        
        annotations = {}
        modalities = self.graph.modalities()
        uris = self.graph.uris()
        for modality in modalities:
            for uri in uris:
                annotations[uri, modality] = Annotation(uri=uri, modality=modality)
        
        for cluster in clusters:
            # find cluster identity
            identities = [n.identifier for n in cluster if isinstance(n, IdentityNode)]
            if identities:
                identity = identities[0]
            else:
                identity = Unknown()
            # add tracks to annotations
            trackNodes = [n for n in cluster if isinstance(n, TrackNode)]
            for n in trackNodes:
                annotations[n.uri, n.modality][n.segment, n.track] = identity
        
        return annotations
        
    
    
        
class GurobiModel(object):
    
    def __init__(self, graph, method=-1, mipGap=1e-4, mipFocus=0, heuristics=0.05,
                       timeLimit=None, 
                       threads=0, quiet=True):
        """
        
        Parameters
        ----------
        mipFocus : {0, 1, 2, 3}
            The MIPFocus parameter allows you to modify your high-level solution
            strategy, depending on your goals. By default, the Gurobi MIP solver
            strikes a balance between finding new feasible solutions and proving
            that the current solution is optimal. If you are more interested in 
            finding feasible solutions quickly, you can select MIPFocus=1. 
            If you believe the solver is having no trouble finding good quality 
            solutions, and wish to focus more attention on proving optimality, 
            select MIPFocus=2. If the best objective bound is moving very slowly
            (or not at all), you may want to try MIPFocus=3 to focus on the 
            bound.
        heuristics : float between 0 and 1
            Determines the amount of time spent in MIP heuristics. You can think
            of the value as the desired fraction of total MIP runtime devoted to
            heuristics (so by default, we aim to spend 5% of runtime on 
            heuristics).
            Larger values produce more and better feasible solutions, at a cost 
            of slower progress in the best bound.
        threads : int
            Controls the number of threads to apply to parallel barrier or 
            parallel MIP. The default value of 0 sets the thread count equal to 
            its maximum value, which is the number of logical cores in the 
            machine.
            While you will generally get the best performance by using all 
            available cores in your machine, there are a few exceptions. One is 
            of course when you are sharing a machine with other jobs. In this 
            case, you should select a thread count that doesn't oversubscribe 
            the machine.
            We have also found that certain classes of MIP models benefit from 
            reducing the thread count, often all the way down to one thread. 
            Starting multiple threads introduces contention for machine 
            resources. For classes of models where the first solution found by 
            the MIP solver is almost always optimal, and that solution isn't 
            found at the root, it is often better to allow a single thread to 
            explore the search tree uncontended.
            Another situation where reducing the thread count can be helpful is 
            when memory is tight. Each thread can consume a significant amount 
            of memory.
        """
                       
                       
        super(GurobiModel, self).__init__()
        self.graph = graph
        self.method = method
        self.mipGap = mipGap
        self.mipFocus = mipFocus
        self.heuristics = heuristics
        self.timeLimit = timeLimit
        self.threads = threads
        self.quiet = quiet
        self.model, self.x = self._model(graph)
    
    
    def _model(self, G):
        """
        G : MultimodalProbabilityGraph
        
        """
        
        model = grb.Model()
        model.setParam('OutputFlag', False)
        
        x = {}
        inodes = G.inodes()
        tnodes = G.tnodes()
        
        nodes = list(inodes) + list(tnodes)
        N = len(nodes)
        
        # nodes pairs
        for i, node in enumerate(nodes):
            x[node, node] = model.addVar(vtype=grb.GRB.BINARY)
            for other_node in nodes[i+1:]:
                x[node, other_node] = model.addVar(vtype=grb.GRB.BINARY)
        
        model.update()
        
        # reflexivity constaints
        for i, node in enumerate(nodes):
            model.addConstr(x[node, node] == 1)
        
        # hard constraints
        for i, node in enumerate(nodes):
            for other_node in nodes[i+1:]:
                if G.has_edge(node, other_node):
                    prob = G[node][other_node][PROBABILITY]
                    if prob in [0,1]:
                        model.addConstr(x[node, other_node] == prob)
        
        # transitivity constraints
        for i in range(N):
            inode = nodes[i]
            for j in range(i+1, N):
                jnode = nodes[j]
                for k in range(j+1, N):
                    knode = nodes[k]
                    model.addConstr(x[jnode,knode]+x[inode,knode]-x[inode,jnode]<=1)
                    model.addConstr(x[inode,jnode]+x[inode,knode]-x[jnode,knode]<=1)
                    model.addConstr(x[inode,jnode]+x[jnode,knode]-x[inode,knode]<=1)
        
        # maximum probability objective
        objective = grb.quicksum([G[inode][tnode][PROBABILITY]*x[inode,tnode]
                                  for inode in inodes for tnode in tnodes
                                  if G.has_edge(inode, tnode)])
        model.setObjective(objective, grb.GRB.MAXIMIZE)
        
        model.setParam(grb.GRB.Param.Method, self.method)
        model.setParam(grb.GRB.Param.MIPFocus, self.mipFocus)
        model.setParam(grb.GRB.Param.Heuristics, self.heuristics)
        model.setParam(grb.GRB.Param.NodefileStart, 0.5)
        model.setParam(grb.GRB.Param.MIPGap, self.mipGap)
        model.setParam(grb.GRB.Param.Threads, self.threads)
        if self.timeLimit is not None:
            model.setParam(grb.GRB.Param.TimeLimit, self.timeLimit)
        model.setParam(grb.GRB.Param.OutputFlag, not self.quiet)
        
        return model, x
    
    def maximizeClusterSize(self):
        """
        Generate clusters as big as possible (taking constraints into account)
        """
        
        cluster = grb.quicksum([self.x[n,m] for (n,m) in self.x])
        
        self.model.setObjective(cluster, grb.GRB.MAXIMIZE)
        self.model.optimize()
        
        return self.getAnnotations()
    
    def minimizeClusterSize(self):
        """
        Generate clusters as small as possible (taking constraints into account)
        """
        
        cluster = grb.quicksum([self.x[n,m] for (n,m) in self.x])
        
        self.model.setObjective(cluster, grb.GRB.MINIMIZE)
        self.model.optimize()
        
        return self.getAnnotations()
    
    def probMaximizeIntraMinimizeInter(self, alpha=0.5):
        """
        Maximize ∑  α.xij.pij + (1-α).(1-xij).(1-pij)
                j>i
        
        Parameters
        ----------
        alpha : float, optional
            0 < α < 1 in above equation
        
        """
        
        intra = grb.quicksum([self.graph[n][m][PROBABILITY]*self.x[n,m] 
                              for (n,m) in self.x 
                              if self.graph.has_edge(n,m)])
                              
        inter = grb.quicksum([(1-self.graph[n][m][PROBABILITY])*(1-self.x[n,m]) 
                              for (n,m) in self.x 
                              if self.graph.has_edge(n,m)])
                              
        self.model.setObjective(alpha*intra+(1-alpha)*inter, grb.GRB.MAXIMIZE)
        self.model.optimize()
        
        return self.getAnnotations()
    
    def weightedProbMaximizeIntraMinimizeInter(self, alpha=0.5, weight='gmean'):
        """
        Maximize ∑  α.wij.xij.pij + (1-α).wij.(1-xij).(1-pij)
                j>i
        
        where wij is the geometric mean of duration of tracks i and j
        
        
        Parameters
        ----------
        alpha : float, optional
            Value of α in above formula
        weight : {'gmean', 'min', 'max'}
            Describes how weights wij are computed from durations di and dj
            - 'gmean' : wij = sqrt(di.dj)
            - 'mean' : wij = .5*(di+dj)
            - 'min' : wij = min(di,dj)
            - 'max' : wij = max(di,dj)
        """
        from scipy.stats import gmean
        
        w = {}
        for n,m in self.x:
            d = []
            if hasattr(n, 'segment'):
                d.append(n.segment.duration)
            if hasattr(m, 'segment'):
                d.append(m.segment.duration)
            if weight == 'gmean':
                w[n,m] = gmean(d) if d else 1.
            elif weight == 'mean':
                w[n,m] = np.mean(d)
            elif weight == 'min':
                w[n,m] = min(d)
            elif weight == 'max':
                w[n,m] = max(d)
        
        intra = grb.quicksum([w[n,m]*self.graph[n][m][PROBABILITY]*self.x[n,m] 
                              for (n,m) in self.x 
                              if self.graph.has_edge(n,m)])
                              
        inter = grb.quicksum([w[n,m]*(1-self.graph[n][m][PROBABILITY])*(1-self.x[n,m]) 
                              for (n,m) in self.x 
                              if self.graph.has_edge(n,m)])
                              
        self.model.setObjective(alpha*intra+(1-alpha)*inter, grb.GRB.MAXIMIZE)
        self.model.optimize()
        
        return self.getAnnotations()
    
    def logProbMaximizeIntraMinimizeInter(self, alpha=0.5):
        """
        Maximize ∑  α.xij.log(pij) + (1-α).(1-xij).log(1-pij)
                j>i
        
        Parameters
        ----------
        alpha : float, optional
            0 < α < 1 in above equation
        
        """
        
        intra = grb.quicksum([np.log(self.graph[n][m][PROBABILITY])*self.x[n,m] 
                              for (n,m) in self.x 
                              if self.graph.has_edge(n,m)
                              and self.graph[n][m][PROBABILITY] > 0])
                              
        inter = grb.quicksum([np.log(1-self.graph[n][m][PROBABILITY])*(1-self.x[n,m]) 
                              for (n,m) in self.x 
                              if self.graph.has_edge(n,m)
                              and self.graph[n][m][PROBABILITY] < 1])
        
        self.model.setObjective((1-alpha)*intra+alpha*inter, grb.GRB.MAXIMIZE)
        self.model.optimize()
        
        return self.getAnnotations()
    
    
    def maximizeModularity(self):
        """
        """
        
        # list of nodes
        nodes = self.graph.nodes()
        
        # adjacency matrix
        P = nx.to_numpy_matrix(self.graph, nodelist=nodes, weight=PROBABILITY)
        P = np.array(P)
        
        # node degree (total weight of {in|out}going edges)
        kin = np.sum(P, axis=0)[:, np.newaxis]
        kout = np.sum(P, axis=1)[:, np.newaxis]
        
        # total edge weight
        t = np.sum(P)
        
        # modularity matrix
        Q = (P - kout*kin.T/t) / t
        
        modularity = grb.quicksum([Q[n,m]*self.x[N,M] for n,N in enumerate(nodes)
                                                      for m,M in enumerate(nodes)
                                                      if (N,M) in self.x])
        
        self.model.setObjective(modularity, grb.GRB.MAXIMIZE)
        self.model.optimize()
        return self.getAnnotations()
    
    
    def getAnnotations(self):
        
        # get clusters
        c = nx.Graph()
        for (n1, n2), var in self.x.iteritems():
            c.add_node(n1)
            c.add_node(n2)
            if var.x == 1.:
                c.add_edge(n1, n2)
        clusters = nx.connected_components(c)
        
        annotations = {}
        modalities = self.graph.modalities()
        uris = self.graph.uris()
        for modality in modalities:
            for uri in uris:
                annotations[uri, modality] = Annotation(uri=uri, modality=modality)
        
        for cluster in clusters:
            # find cluster identity
            identities = [n.identifier for n in cluster if isinstance(n, IdentityNode)]
            if identities:
                identity = identities[0]
            else:
                identity = Unknown()
            # add tracks to annotations
            trackNodes = [n for n in cluster if isinstance(n, TrackNode)]
            for n in trackNodes:
                annotations[n.uri, n.modality][n.segment, n.track] = identity
        
        return annotations
    

    
