import gurobipy as grb
import numpy as np
import networkx as nx
import pyfusion.normalization.bayes

def clusters_from_x(N, x):
    
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

def generic_clustering_problem(N, problem_name):
    """
    
    Parameters
    ----------
    N : int
        Number of clustered items
    problem_name : str
        Problem identifier
    
    Returns
    -------
    model : gurobipy.Model
        Gurobi model with no objective yet.
    x : dict
        Gurobi variables
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
    t = {}
    for i in range(N):
        for j in range(N):
            for k in range(N):
                t[i,j,k] = (1-x[i,j])+(1-x[j,k]) >= (1-x[i,k])
                name = "t_%d_%d_%d" % (i, j, k)
                model.addConstr(t[i,j,k], name)
    
    # return the model & its variables
    return model, x

def io_log_prob_objective(P, alpha, x):
    
    N, N = P.shape
    
    # objective
    h1 = np.maximum(-1e10, np.log(P))
    h0 = np.maximum(-1e10, np.log(1 - P))
    objective = grb.quicksum([alpha     * h1[i,j] * x[i,j] +
                              (1-alpha) * h0[i,j] * (1-x[i,j])
                             for i in range(N) for j in range(i+1, N)])
    return objective

def io_prob_objective(P, alpha, x):
    
    N, N = P.shape
    
    # objective
    objective = grb.quicksum([alpha     * P[i,j]     * x[i,j] +
                              (1-alpha) * (1-P[i,j]) * (1-x[i,j])
                              for i in range(N) for j in range(i+1, N)])
    return objective


def modularity_objective(P, x):
    """
    
    Parameters
    ----------
    
    
    """
    N, N = P.shape
    
    # total weights in graph
    m = np.sum(P)
    
    # node degree (total weight of {in|out}going edges)
    kin = np.sum(P, axis=0)[:, np.newaxis]
    kout = np.sum(P, axis=1)[:, np.newaxis]
    
    # modularity matrix
    Q = (P - kout*kin.T/m) / m
    
    # objective
    objective = grb.quicksum([Q[i, j] * x[i, j] 
                              for i in range(N) for j in range(N)])
    
    return objective

def io_log_prob(P, alpha):
    
    N, N = P.shape
    
    # build generic clustering problem
    # with symmetry & transitivity constraints
    model, x = generic_clustering_problem(N, "io_log_prob")
    
    # objective
    objective = io_log_prob_objective(P, alpha, x)
    model.setObjective(objective, grb.GRB.MAXIMIZE)
    
    # quietly optimize
    # model.setParam('OutputFlag', False)
    model.optimize()
    
    return clusters_from_x(N, x)

def io_log_prob(P, alpha):
    
    N, N = P.shape
    
    # build generic clustering problem
    # with symmetry & transitivity constraints
    model, x = generic_clustering_problem(N, "io_prob")
    
    # objective
    objective = io_prob_objective(P, alpha, x)
    model.setObjective(objective, grb.GRB.MAXIMIZE)
    
    # quietly optimize
    # model.setParam('OutputFlag', False)
    model.optimize()
    
    return clusters_from_x(N, x)


def q_prob(P):
    
    N, N = P.shape
    
    # build generic clustering problem
    # with symmetry & transitivity constraints
    model, x = generic_clustering_problem(N, "q_prob")
    
    # objective
    objective = modularity_objective(P, x)
    model.setObjective(objective, grb.GRB.MAXIMIZE)
    
    # quietly optimize
    # model.setParam('OutputFlag', False)
    model.optimize()
    
    return clusters_from_x(N, x)


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
    
    def __call__(self, annotation, feature, alpha=None):
        
        # get tracks similarity & make it a posterior probability P
        X = self._get_X(annotation, feature)
        N, _ = X.shape
        P = self.posterior.transform(X.reshape((-1, 1))).reshape((N, N))
        
        # optimization
        # clusters = q_prob(P)
        # clusters = io_prob(P)
        clusters = io_log_prob(P, alpha)
        
        translation = {}
        for c, cluster in enumerate(clusters):
            for i in cluster:
                translation[i] = c
        
        # build new annotation based on this...
        new_annotation = annotation.empty()
        for i, (Si, Ti, _) in enumerate(annotation.iterlabels()):
            new_annotation[Si, Ti] = translation[i]
        
        return new_annotation
        