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

try:
    import os
    import socket
    os.putenv('GRB_LICENSE_FILE',
              "%s/licenses/%s.lic" % (os.getenv('GUROBI_HOME'),
                                      socket.gethostname()))
    import gurobipy as grb
except Exception, e:
    import sys
    sys.stderr.write('Cannot initialize Gurobi.\n')

import numpy as np


class ILPClusteringMixin(object):
    """
    MIP problem solving mixin.

    Assumes instance has the following two attributes:

    instance.model : `grb.Model`
        Full Gurobi MIP problem
    instance.x : dict
        Dictionary containing the variables of the MIP problem `model`

    """

    def __init__(self, items, similarity, get_similarity=None, **kwargs):
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

        # create empty Gurobi model (and shut it up)
        self.model = grb.Model()
        self.model.setParam(grb.GRB.Param.OutputFlag, False)

        # one binary variable per item pair
        self.x = {}
        for i in enumerate(items):
            for j in items:
                self.x[i, j] = self.model.addVar(vtype=grb.GRB.BINARY)

        # Gurobi updates model lazily
        self.model.update()

        # Default assumes `similarity` is a pandas `DataFrame`
        if not get_similarity:
            get_similarity = lambda i, j, S: S[i][j]

        # set_constraints method is not provided by this base class
        # it must be provided by a ConstraintMixin
        self.set_constraints(items, similarity, get_similarity, **kwargs)

        # set_objective method is not provided by this base class
        # it must be provided by a ObjectiveMixin
        self.set_objective(items, similarity, get_similarity, **kwargs)

        return self

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
        time_limit : int, optional
        threads : int, optional
        verbose : boolean, optional

        Returns
        -------
        solution : dict


        """

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

        # TODO: initial solution

        # Gurobi powaaaaa!
        self.model.optimize()

        # read solution
        solution = {}
        for key, variable in self.x.iteritems():
            solution[key] = variable.x

        return solution

    def dump(self, path):
        self.model.dump(path)


class FinkelConstraintMixin(object):
    """

    """

    def set_constraints(self, items, similarity, get_similarity, **kwargs):

        # number of items
        N = len(items)

        # reflexivity constraints
        # O(N) complexity
        for I in items:
            constr = self.x[I, I] == 1
            self.model.addConstr(constr)

        # # hard constraints
        # for i, item in enumerate(items):
        #     for other_item in items[i+1:]:
        #         s = get_similarity(item, other_item, similarity)
        #         if s in [0, 1]:
        #             self.model.addConstr(self.x[item, other_item] == s)

        # symmetry constraints
        # O(N^2) complexity
        for i, I in enumerate(items):
            for J in items[i+1:]:
                constr = self.x[I, J] == self.x[J, I]
                self.model.addConstr(constr)

        # transitivity constraints
        # O(N^3) complexity
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

        return self


class INTRAinterObjectiveMixin(object):
    """
    Maximize ∑  α.xij.pij + (1-α).(1-xij).(1-pij)
            i,j
    """

    def set_objective(self, items, similarity, get_similarity, alpha=0.5, **kwargs):
        """
        Set objective function

        Parameters
        ----------
        alpha : float, optional
            Set α in above equation (0 < α < 1)

        """

        # intra-cluster similarity
        intraSim = grb.quicksum([get_similarity(I, J, similarity)*self.x[I, J]
                                 for (I, J) in self.x
                                 if not np.isnan(get_similarity(I, J, similarity))])

        # inter-cluster similarity
        interSim = grb.quicksum([get_similarity(I, J, similarity)*(1-self.x[I, J])
                                 for (I, J) in self.x
                                 if not np.isnan(get_similarity(I, J, similarity))])

        # jointly maximize intra-cluster similarity & minimize inter-cluster one
        self.model.setObjective(alpha*intraSim + (1-alpha)*interSim,
                                grb.GRB.MAXIMIZE)

        return self


class DupuyConstraintMixin(object):
    """

    Dupuy et al. ...
    """

    def set_constrains(self, items, similarity, get_similarity, delta=None, **kwargs):

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
                constr = sCI * self.x[C, I] >= self.delta
                self.model.addConstr(constr)

        # Equation 1.5 (missing in Dupuy et al.)
        # activate a centroid as soon as an item is associated to it
        for C in items:
            for I in items:
                constr = self.x[C, C] >= self.x[C, I]
                self.model.addConstr(constr)

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

        return self
