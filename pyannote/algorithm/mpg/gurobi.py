import os
import socket
os.putenv('GRB_LICENSE_FILE', 
          "%s/licenses/%s.lic" % (os.getenv('GUROBI_HOME'),
                                  socket.gethostname()))

import gurobipy as grb
from graph import PROBABILITY
from pyannote.base.annotation import Annotation, Unknown
from node import IdentityNode, TrackNode

class GurobiModel(object):
    def __init__(self, graph, method=-1, mipGap=1e-4, timeLimit=None, 
                          threads=None, quiet=True):
        super(GurobiModel, self).__init__()
        self.graph = graph
        self.method = method
        self.mipGap = mipGap
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
            for other_node in nodes[i+1:]:
                x[node, other_node] = model.addVar(vtype=grb.GRB.BINARY)
        
        model.update()
        
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
        if self.threads is not None:
            model.setParam(grb.GRB.Param.Threads, self.threads)
        model.setParam(grb.GRB.Param.NodefileStart, 0.5)
        model.setParam(grb.GRB.Param.MIPGap, self.mipGap)
        if self.timeLimit is not None:
            model.setParam(grb.GRB.Param.TimeLimit, self.timeLimit)
        model.setParam(grb.GRB.Param.OutputFlag, not self.quiet)
        
        return model, x
    
    def probMaximizeIntraMinimizeInter(self, alpha=0.5):
        
        intra = grb.quicksum([self.graph[n][m][PROBABILITY]*self.x[n,m] 
                              for (n,m) in self.x 
                              if self.graph.has_edge(n,m)])
                              
        inter = grb.quicksum([(1-self.graph[n][m][PROBABILITY])*(1-self.x[n,m]) 
                              for (n,m) in self.x 
                              if self.graph.has_edge(n,m)])
                              
        self.model.setObjective(alpha*intra+(1-alpha)*inter, grb.GRB.MAXIMIZE)
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
    

    