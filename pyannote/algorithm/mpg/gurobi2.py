#!/usr/bin/env python
# encoding: utf-8

# Copyright 2013 Herve BREDIN (bredin@limsi.fr)

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


import sys
import numpy as np
import networkx as nx

# initialize Gurobi solver
try:
    # try to rely on the existing GRB_LICENSE_FILE variable first
    import gurobipy as grb
except:
    # otherwise, try hard-coded license file
    import os
    import socket
    pathToLicense = "%s/licenses/%s.lic" % (os.getenv('GUROBI_HOME'),
                                            socket.gethostname())
    os.putenv('GRB_LICENSE_FILE', pathToLicense)
    try:
        import gurobipy as grb
    except:
        sys.stderr.write('Cannot initialize Gurobi solver.')


class ILPClusteringMixin(object):
    """
    MIP problem solving mixin.

    Assumes instance has the following two attributes:

    instance.model : `grb.Model`
        Full Gurobi MIP problem
    instance.x : dict
        Dictionary containing the variables of the MIP problem `model`

    """

    def init_model(self):
        """"""
        # create empty Gurobi model (and shut the **** up)
        self.model = grb.Model()
        self.model.setParam(grb.GRB.Param.OutputFlag, False)

    def init_variables(self, items):
        """"""

        # one binary variable per item pair
        self.x = {}

        for I in items:
            for J in items:
                self.x[I, J] = self.model.addVar(vtype=grb.GRB.BINARY)

        self.model.update()

    def update_model(self):
        """"""

        self.model.update()

    def __init__(self, items, similarity, get_similarity=None,
                 debug=False, **kwargs):
        """
        Create MIP clustering problem

        Parameters
        ----------
        items : hashables iterable

        similarity :

        get_similarity : func, optional
            Takes three arguments item1, item2 and similarity
            and returns the similarity between item1 and item2
            or NaN when the similarity is not available.

        """

        super(ILPClusteringMixin, self).__init__()

        # create empty Gurobi model
        self.init_model()

        # add variables
        self.init_variables(items)

        # Gurobi updates model lazily
        self.update_model()

        # Default assumes `similarity` is a pandas `DataFrame`
        if not get_similarity:
            get_similarity = lambda i, j, S: S[i][j]

        # set_constraints method is not provided by this base class
        # it must be provided by a ConstraintMixin
        if debug:
            sys.stderr.write("DEBUG: set constraints\n")
        self.set_constraints(items, similarity, get_similarity,
                             debug=debug, **kwargs)

        # set_objective method is not provided by this base class
        # it must be provided by a ObjectiveMixin
        if debug:
            sys.stderr.write("DEBUG: set objective\n")
        self.set_objective(items, similarity, get_similarity,
                           debug=debug, **kwargs)

    def add_reflexivity_constraints(self, items):
        """Add reflexivity constraints (I~I, for all I)"""

        for I in items:
            constr = self.x[I, I] == 1
            self.model.addConstr(constr)

    def add_hard_constraints(self, items, similarity, get_similarity):
        """Add hard constraints

        If sim(I, J) = 0, then I|J.
        If sim(I, J) = 1, then I~J.
        """

        N = len(items)
        for i in range(N):
            I = items[i]
            for j in range(i+1, N):
                J = items[j]
                s = get_similarity(I, J, similarity)
                if s in [0, 1]:
                    constr = self.x[I, J] == s
                    self.model.addConstr(constr)

    def add_symmetry_constraints(self, items):
        """Add symmetry constratins

        For any pair (I, J), I~J implies J~I
        """

        N = len(items)
        for i in range(N):
            I = items[i]
            for j in range(i+1, N):
                J = items[j]
                constr = self.x[I, J] == self.x[J, I]
                self.model.addConstr(constr)

    def add_transitivity_constraints(self, items):
        """Add transitivity contraints

        For any triplet (I,J,K), I~J and J~K implies I~K
        """

        N = len(items)
        for i in range(N):
            I = items[i]
            for j in range(i+1, N):
                J = items[j]
                for k in range(j+1, N):
                    K = items[k]
                    constr = self.x[J, K]+self.x[I, K]-self.x[I, J] <= 1
                    self.model.addConstr(constr)
                    constr = self.x[I, J]+self.x[I, K]-self.x[J, K] <= 1
                    self.model.addConstr(constr)
                    constr = self.x[I, J]+self.x[J, K]-self.x[I, K] <= 1
                    self.model.addConstr(constr)

    def add_asymmetric_transitivity_constraints(self, tracks, identities):
        """Add asymmetric transitivity constraints

        For any pair of tracks (T, S) and any identity I,
            T~I and T~S implies S~I

        However, T~I and S~I does not imply T~S
        """

        Nt = len(tracks)
        Ni = len(identities)

        for i in range(Ni):
            I = identities[i]
            for t in range(Nt):
                T = tracks[t]
                for s in range(t+1, Nt):
                    S = tracks[s]
                    constr = self.x[T, I]+self.x[T, S]-self.x[S, I] <= 1
                    self.model.addConstr(constr)
                    constr = self.x[S, I]+self.x[T, S]-self.x[T, I] <= 1
                    self.model.addConstr(constr)

    def get_inter_cluster_dissimilarity(self, items,
                                        similarity, get_similarity):
        """Inter-cluster dissimilarity:  ∑ (1-xij).(1-pij)
                                        i,j

        """
        values = [(1-get_similarity(I, J, similarity))*(1-self.x[I, J])
                  for I in items for J in items
                  if not np.isnan(get_similarity(I, J, similarity))]
        return grb.quicksum(values)

    def get_intra_cluster_similarity(self, items,
                                     similarity, get_similarity):
        """Intra-cluster similarity: ∑  xij.pij
                                    i,j
        """
        values = [get_similarity(I, J, similarity)*self.x[I, J]
                  for I in items for J in items
                  if not np.isnan(get_similarity(I, J, similarity))]
        return grb.quicksum(values)

    def get_identity_similarity(self, tracks, identities,
                                similarity, get_similarity):
        """
         ∑  xti.pti
        t,i
        """
        values = [get_similarity(T, I, similarity)*self.x[T, I]
                  for T in tracks for I in identities
                  if not np.isnan(get_similarity(T, I, similarity))]
        return grb.quicksum(values)

    def get_identity_dissimilarity(self, tracks, identities,
                                   similarity, get_similarity):
        """
         ∑ (1-xti).(1-pti)
        t,i
        """
        values = [(1-get_similarity(T, I, similarity))*(1-self.x[T, I])
                  for T in tracks for I in identities
                  if not np.isnan(get_similarity(T, I, similarity))]
        return grb.quicksum(values)

    def solve(self, init=None,
              method=None, mip_focus=None, heuristics=None,
              mip_gap=None, time_limit=None,
              threads=None, verbose=False):
        """
        Solve ILP problem

        Parameters
        ----------
        init : dict, optional
        method : {}, optional
        mip_focus : {}, optional
        heuristics : {}, optional
        mip_gap : float, optional
        time_limit : float, optional
            Time limit in seconds.
        threads : int, optional
        verbose : boolean, optional

        Returns
        -------
        solution : dict


        """

        # initial solution
        if init:
            for (I, J), variable in init.iteritems():
                self.x[I, J].start = variable

        # Gurobi behavior
        if method:
            self.model.setParam(grb.GRB.Param.Method, method)
        if mip_focus:
            self.model.setParam(grb.GRB.Param.MIPFocus, mip_focus)
        if heuristics:
            self.model.setParam(grb.GRB.Param.Heuristics, heuristics)

        # Stopping criteria
        if mip_gap:
            self.model.setParam(grb.GRB.Param.MIPGap, mip_gap)
        if time_limit:
            self.model.setParam(grb.GRB.Param.TimeLimit, time_limit)

        if threads:
            self.model.setParam(grb.GRB.Param.Threads, threads)

        self.model.setParam(grb.GRB.Param.OutputFlag, verbose)

        # Gurobi powaaaaa!
        self.model.optimize()

        # read solution
        solution = {}
        for key, variable in self.x.iteritems():
            solution[key] = variable.x

        # convert solution to list of clusters
        c = nx.Graph()
        for (I, J), same_cluster in solution.iteritems():
            c.add_node(I),
            c.add_node(J)
            if same_cluster:
                c.add_edge(I, J)
        clusters = nx.connected_components(c)

        return clusters

    def dump(self, path):
        """
        Dump Gurobi model to file (for debugging purpose)

        Parameters
        ----------
        path : str
            Where to dump Gurobi model

        """

        # model (lazy) update
        self.model.update()

        # dump to file
        self.model.write(path)


class FinkelConstraintMixin(ILPClusteringMixin):
    """

    """

    def set_contraints(self, items, similarity, get_similarity, debug=False):

        if debug:
            sys.stderr.write("DEBUG: add reflexivity constraints\n")
        self.add_reflexivity_constraints(items)

        if debug:
            sys.stderr.write("DEBUG: add hard constraints\n")
        self.add_hard_constraints(items, similarity, get_similarity)

        if debug:
            sys.stderr.write("DEBUG: add symmetry constraints\n")
        self.add_symmetry_constraints(items)

        if debug:
            sys.stderr.write("DEBUG: add transitivity constraints\n")
        self.add_transitivity_constraints(items)

        self.model.update()

        return self


class INTRAinterObjectiveMixin(object):
    """
    Maximize ∑  α.xij.pij + (1-α).(1-xij).(1-pij)
            i,j
    """

    def set_objective(self, items, similarity, get_similarity,
                      alpha=0.5, **kwargs):
        """
        Set objective function

        Parameters
        ----------
        alpha : float, optional
            Set α in above equation (0 < α < 1)

        """

        # intra-cluster similarity
        intraSim = grb.quicksum(
            [get_similarity(I, J, similarity)*self.x[I, J] for (I, J) in self.x
             if not np.isnan(get_similarity(I, J, similarity))])

        # inter-cluster similarity
        interSim = grb.quicksum(
            [(1-get_similarity(I, J, similarity))*(1-self.x[I, J])
             for (I, J) in self.x
             if not np.isnan(get_similarity(I, J, similarity))])

        # jointly maximize intra-cluster similarity
        # and minimize inter-cluster one
        self.model.setObjective(alpha*intraSim + (1-alpha)*interSim,
                                grb.GRB.MAXIMIZE)

        # model (lazy) update
        self.model.update()

        return self


class DupuyConstraintMixin(object):
    """

    Dupuy et al. ...
    """

    def set_constraints(self, items, similarity, get_similarity,
                        delta=0.5, **kwargs):
        """

        Parameters
        ----------
        items :

        similarity :

        get_similarity :

        delta : float, optional
            Prevent items with similarity lower than delta from ending
            in the same cluster. Must fall in [0, 1] range.

        """
        # Equation 1.3 (in Dupuy et al., JEP'12)
        # every item is associated to exactly one centroid
        for J in items:
            constr = grb.quicksum([self.x[C, J] for C in items]) == 1
            self.model.addConstr(constr)

        # Equation 1.4 (in Dupuy et al., JEP'12)
        # prevent items from being associated to a dissimilar centroid
        for C in items:
            for I in items:
                sCI = get_similarity(C, I, similarity)
                if np.isnan(sCI):
                    continue
                constr = (1-sCI) * self.x[C, I] <= (1-delta)
                self.model.addConstr(constr)

        # Equation 1.5 (missing in Dupuy et al.)
        # activate a centroid as soon as an item is associated to it
        for C in items:
            for I in items:
                constr = self.x[C, C] >= self.x[C, I]
                self.model.addConstr(constr)

        # model (lazy) update
        self.model.update()

        return self


class DupuyObjectiveMixin(object):
    """

    """

    def set_objective(self, items, similarity, get_similarity, **kwargs):
        """

        """

        # number of items
        N = len(items)

        # number of activated centroids
        centroids = grb.quicksum([self.x[C, C] for C in items])

        # cluster cohesion (ie total similarity to centroids)
        cohesion = grb.quicksum([get_similarity(C, I, similarity)*self.x[C, I]
                                 for C in items for I in items if C != I])

        # according to a discussion I had with Mickael Rouvier,
        # F (in Dupuy et al. 2012) is actually the sum over all items
        # of the maximum distance to all other items
        # in short, F = N

        # minimize both number of centroids and dispersion
        self.model.setObjective(centroids - 1./N * cohesion, grb.GRB.MINIMIZE)

        # model (lazy) update
        self.model.update()

        return self
