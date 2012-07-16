
import gurobipy
import numpy as np
import networkx as nx
import pyfusion.normalization.bayes

class IntegerLinearProgramming(object):
    
    def __init__(self, **kwargs):
        super(IntegerLinearProgramming, self).__init__()
        self.mmx_setup(**kwargs)
    
    def _get_y(self, annotation):
        """
        Get diarization groundtruth
        
        Parameters
        ----------
        annotation : :class:`Annotation`
        
        Returns
        -------
        y : numpy array (num_tracks, num_tracks)
            y[i, j] = 1 if tracks i & j should be in the same cluster
            y[i, j] = 0 if tracks i & j must not be in the same cluster
            y[i, j] = -1 if no definitive information is available
        """
        
        # total number of tracks
        N = len([_ for _ in annotation.iterlabels()])
        
        # intialize clustering status as -1 (unknown)
        y = -np.ones((N,N), dtype=np.int8)
        
        for i, (Si, _, Li) in enumerate(annotation.iterlabels()):
            
            # if more than one track -- don't know which is which
            if len(annotation[Si, :]) > 1:
                y[i, :] = -1
                y[:, i] = -1
            
            for j, (Sj, _, Lj) in enumerate(annotation.iterlabels()):
                if j > i:
                    break
                if len(annotation[Sj, :]) > 1:
                    y[:, j] = -1
                    y[j, :] = -1
                    continue
                y[i, j] = (Li == Lj)
                y[j, i] = y[i, j]
        
        return y
    
    
    def _get_X(self, annotation, feature):
        """
        
        """
        
        # one model per label
        models = {label : self.mmx_fit(label, annotation=annotation,
                                              feature=feature)
                  for label in annotation.labels()}
        
        # total number of tracks
        N = len([_ for _ in annotation.iterlabels()])
        
        # similarity between tracks
        X = np.empty((N, N), dtype=np.float32)
        for i, (_, _, Li) in enumerate(annotation.iterlabels()):
            for j, (_, _, Lj) in enumerate(annotation.iterlabels()):
                if self.mmx_symmetric() and j > i:
                    break
                X[i, j] = self.mmx_compare(Li, Lj, models=models)
                if self.mmx_symmetric():
                    X[j, i] = X[i, j]
        
        return X
    
    def train(self, annotations, features):
        """
        
        Parameters
        ----------
        annotations : list of :class:`Annotation`
        features : list of :class:`Feature`
        
        
        """
        
        X = np.concatenate([self._get_X(annotation, features[a]).reshape((-1,1))
                            for a, annotation in enumerate(annotations)])
        y = np.concatenate([self._get_y(annotation).reshape((-1, 1)) 
                            for a, annotation in enumerate(annotations)])
        self.posterior = pyfusion.normalization.bayes.Posterior(pos_label=1,
                                                                neg_label=0)
        self.posterior.fit(X, y=y)
        
    
    def _get_ipl(self, P, alpha=None):
        """
        
        Parameters
        ----------
        P : array-like (num_tracks, num_tracks)
            P[i, j] is the probability for i & j to be in the same cluster
        alpha : float, optional
            Defaults to 1./num_tracks
        
        """
        N, N = P.shape
        
        if alpha is None:
            alpha = 1./N
        
        # gurobi model
        m = gurobipy.Model("ipl")
        
        # model variables
        # xij = 1 <==> i & j in the same cluster
        x = {}
        for i in range(N):
            for j in range(N):
                x[i, j] = m.addVar(vtype=gurobipy.GRB.BINARY,
                                   name="x_%02d_%02d" % (i,j))
        m.update()
        
        # objective
        # maximize intra-cluster probability 
        # minimize inter-cluster probability
        h1 = np.maximum(-1e10, np.log(P))
        h0 = np.maximum(-1e10, np.log(1 - P))
        obj = gurobipy.quicksum(h1[i,j]*x[i,j] + alpha*h0[i, j]*(1-x[i,j])
                                for i in range(N) for j in range(N))
        m.setObjective(obj, gurobipy.GRB.MAXIMIZE)
        
        # each label in its own cluster
        o = {}
        for i in range(N):
            o[i] = m.addConstr(x[i,i]==1)
            
        # symmetry constraint
        s = {}
        for i in range(N):
            for j in range(i+1, N):
                s[i,j] = m.addConstr(x[i,j]==x[j,i])
        
        # transitivity constraints
        t = {}
        for i in range(N):
            for j in range(N):
                for k in range(N):
                    t[i,j,k] = m.addConstr((1-x[i,j])+(1-x[j,k]) >= (1-x[i,k]))
        
        return x, m
        
    def __call__(self, annotation, feature, alpha=None):
        
        # get tracks similarity & make it a posterior probability P
        X = self._get_X(annotation, feature)
        N, _ = X.shape
        P = self.posterior.transform(X.reshape((-1, 1))).reshape((N, N))
        
        # optimization
        x, m = self._get_ipl(P, alpha=alpha)
        m.optimize()
        
        # read results as a graph
        # one node per label, edges between same-cluster labels
        g = nx.Graph()
        for i, _ in enumerate(annotation.iterlabels()):
            g.add_node(i)
            for j, _ in enumerate(annotation.iterlabels()):
                if j > i:
                    break
                if x[i, j].x:
                    g.add_edge(i, j)
        
        # find clusters (connected components in graph)
        clusters = nx.connected_components(g)
        translation = {}
        for c, cluster in enumerate(clusters):
            for i in cluster:
                translation[i] = c
        
        # build new annotation based on this...
        new_annotation = annotation.empty()
        for i, (Si, Ti, _) in enumerate(annotation.iterlabels()):
            new_annotation[Si, Ti] = translation[i]
        
        return new_annotation
        