#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012-2013 Herve BREDIN (bredin@limsi.fr)

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


import itertools
import numpy as np
import networkx as nx
try:
    import gurobipy as grb
except:
    pass
try:
    import pulp
except:
    pass


class ILPClustering(object):

    """

    Parameters
    ----------
    items :
    similarity :
    get_similarity : func, optional

    """

    def __init__(self, solver='pulp'):

        super(ILPClustering, self).__init__()

        self.solver = solver

    # =================================================================
    # VARIABLES & PROBLEM
    # =================================================================

    def add_pair_variables(self, items):
        """Add one variable per pair of items"""

        if self.solver == 'gurobi':
            self._gurobi_add_pair_variables(items)

        if self.solver == 'pulp':
            self._pulp_add_pair_variables(items)

        return self

    def _gurobi_add_pair_variables(self, items):
        """Add one variable per pair of items"""

        self.x = {}

        for I, J in itertools.product(items, repeat=2):
            self.x[I, J] = self.model.addVar(vtype=grb.GRB.BINARY)

        self.model.update()

        return self

    def _pulp_add_pair_variables(self, items):
        """Add one variable per pair of items"""

        self.x = {}

        for I, J in itertools.product(items, repeat=2):
            name = "%s / %s" % (I, J)
            self.x[I, J] = pulp.LpVariable(name, cat=pulp.constants.LpBinary)

        return self

    def reset_problem(self, items):
        """
        items : iterable

        """

        # empty (silent) model
        if self.solver == 'gurobi':
            self.model = grb.Model('Person instance graph clustering')
            self.model.setParam(grb.GRB.Param.OutputFlag, False)

        if self.solver == 'pulp':
            # empty problem
            self.problem = pulp.LpProblem(
                name='Person instance graph clustering',
                sense=pulp.constants.LpMaximize
            )

        self.add_pair_variables(items)

        return self

    # =================================================================
    # CONSTRAINTS
    # =================================================================

    # Reflexivity constraints
    # ~~~~~~~~~~~~~~~~~~~~~~~

    def add_reflexivity_constraints(self, items):
        """Add reflexivity constraints (I~I, for all I)"""

        if self.solver == 'gurobi':
            return self._gurobi_add_reflexivity_constraints(items)

        if self.solver == 'pulp':
            return self._pulp_add_reflexivity_constraints(items)

    def _gurobi_add_reflexivity_constraints(self, items):

        for I in items:
            constr = self.x[I, I] == 1
            self.model.addConstr(constr)

        self.model.update()

        return self

    def _pulp_add_reflexivity_constraints(self, items):

        for I in items:
            name = "Reflexivity constraint (%s)" % (repr(I))
            self.problem += self.x[I, I] == 1, name

        return self

    # Symmetry constraints
    # ~~~~~~~~~~~~~~~~~~~~

    def add_symmetry_constraints(self, items):
        """Add symmetry constratins

        For any pair (I, J), I~J implies J~I
        """
        if self.solver == 'gurobi':
            return self._gurobi_add_symmetry_constraints(items)

        if self.solver == 'pulp':
            return self._pulp_add_symmetry_constraints(items)

    def _pulp_add_symmetry_constraints(self, items):

        for I, J in itertools.combinations(items, 2):
            name = "Symmetry constraint (%s / %s)" % (I, J)
            self.problem += self.x[I, J] - self.x[J, I] == 0, name

        return self

    def _gurobi_add_symmetry_constraints(self, items):

        for I, J in itertools.combinations(items, 2):
            constr = self.x[I, J] == self.x[J, I]
            self.model.addConstr(constr)

        self.model.update()

        return self

    # Transitivity constraints
    # ~~~~~~~~~~~~~~~~~~~~~~~~

    def add_transitivity_constraints(self, items):
        """Add transitivity contraints

        For any triplet (I,J,K), I~J and J~K implies I~K
        """

        if self.solver == 'gurobi':
            self._gurobi_add_transitivity_constraints(items)

        if self.solver == 'pulp':
            self._pulp_add_transitivity_constraints(items)

        return self

    def _pulp_add_transitivity_constraints(self, items):
        """Add transitivity contraints

        For any triplet (I,J,K), I~J and J~K implies I~K
        """

        for I, J, K in itertools.combinations(items, 3):

            name = "Transitivity constraint (%s / %s / %s)" % (I, K, J)
            self.problem += self.x[J, K]+self.x[I, K]-self.x[I, J] <= 1, name

            name = "Transitivity constraint (%s / %s / %s)" % (I, J, K)
            self.problem += self.x[I, J]+self.x[I, K]-self.x[J, K] <= 1, name

            name = "Transitivity constraint (%s / %s / %s)" % (J, I, K)
            self.problem += self.x[I, J]+self.x[J, K]-self.x[I, K] <= 1, name

        return self

    def _gurobi_add_transitivity_constraints(self, items):
        """Add transitivity contraints

        For any triplet (I,J,K), I~J and J~K implies I~K
        """

        for I, J, K in itertools.combinations(items, 3):

            constr = self.x[J, K]+self.x[I, K]-self.x[I, J] <= 1
            self.model.addConstr(constr)

            constr = self.x[I, J]+self.x[I, K]-self.x[J, K] <= 1
            self.model.addConstr(constr)

            constr = self.x[I, J]+self.x[J, K]-self.x[I, K] <= 1
            self.model.addConstr(constr)

        self.model.update()

        return self

    # Asymmetric transitivity constraints
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def add_asymmetric_transitivity_constraints(self, tracks, identities):
        """Add asymmetric transitivity constraints

        For any pair of tracks (T, S) and any identity I,
            T~I and T~S implies S~I

        However, T~I and S~I does not imply T~S
        """

        if self.solver == 'gurobi':
            self._gurobi_add_asymmetric_transitivity_constraints(tracks, identities)

        if self.solver == 'pulp':
            self._pulp_add_asymmetric_transitivity_constraints(tracks, identities)

        return self

    def _pulp_add_asymmetric_transitivity_constraints(
        self, tracks, identities
    ):
        """Add asymmetric transitivity constraints

        For any pair of tracks (T, S) and any identity I,
            T~I and T~S implies S~I

        However, T~I and S~I does not imply T~S
        """

        for I in identities:

            for T, S in itertools.combinations(tracks, 2):

                name = "Asymmetric transitivity constraint (%s / %s / %s)" % (I, S, T)
                constr = self.x[T, I]+self.x[T, S]-self.x[S, I] <= 1
                self.problem += constr, name

                name = "Asymmetric transitivity constraint (%s / %s / %s)" % (I, T, S)
                constr = self.x[S, I]+self.x[T, S]-self.x[T, I] <= 1
                self.problem += constr, name

        return self

    def _gurobi_add_asymmetric_transitivity_constraints(
        self, tracks, identities
    ):
        """Add asymmetric transitivity constraints

        For any pair of tracks (T, S) and any identity I,
            T~I and T~S implies S~I

        However, T~I and S~I does not imply T~S
        """

        for I in identities:

            for T, S in itertools.combinations(tracks, 2):

                constr = self.x[T, I]+self.x[T, S]-self.x[S, I] <= 1
                self.model.addConstr(constr)

                constr = self.x[S, I]+self.x[T, S]-self.x[T, I] <= 1
                self.model.addConstr(constr)

        self.model.update()

        return self

    # Hard constraints
    # ~~~~~~~~~~~~~~~~

    def add_hard_constraints(self, items, get_similarity):
        """Add hard constraints

        If sim(I, J) = 0, then I|J.
        If sim(I, J) = 1, then I~J.
        """

        if self.solver == 'gurobi':
            self._gurobi_add_hard_constraints(items, get_similarity)

        if self.solver == 'pulp':
            self._pulp_add_hard_constraints(items, get_similarity)

        return self

    def _pulp_add_hard_constraints(self, items, get_similarity):
        """Add hard constraints

        If sim(I, J) = 0, then I|J.
        If sim(I, J) = 1, then I~J.
        """

        for I, J in itertools.combinations(items, 2):

            s = get_similarity(I, J)
            if s in [0, 1]:

                name = "Hard constraint (%s / %s)" % (I, J)
                constr = self.x[I, J] == s
                self.problem += constr, name

        return self

    def _gurobi_add_hard_constraints(self, items, get_similarity):
        """Add hard constraints

        If sim(I, J) = 0, then I|J.
        If sim(I, J) = 1, then I~J.
        """

        for I, J in itertools.combinations(items, 2):

            s = get_similarity(I, J)
            if s in [0, 1]:

                constr = self.x[I, J] == s
                self.model.addConstr(constr)

        self.model.update()

        return self

    # Exclusivity constraints
    # ~~~~~~~~~~~~~~~~~~~~~~~

    def add_exclusivity_constraints(self, sources, targets):
        """Add exclusivity constraints

        Any source element S can be connected to at most one target element T.
        """

        if self.solver == 'gurobi':
            self._gurobi_add_exclusivity_constraints(sources, targets)

        if self.solver == 'pulp':
            self._pulp_add_exclusivity_constraints(sources, targets)

        return self

    def _pulp_add_exclusivity_constraints(self, sources, targets):

        if targets:
            for T in sources:

                name = "Exclusivity constraint (%s)" % T
                constr = sum([self.x[T, I] for I in targets]) <= 1
                self.problem += constr, name

        return self

    def _gurobi_add_exclusivity_constraints(self, sources, targets):

        if targets:
            for T in sources:
                constr = grb.quicksum([self.x[T, I] for I in targets]) <= 1
                self.model.addConstr(constr)

        self.model.update()

        return self

    # =================================================================
    # OBJECTIVE FUNCTIONS
    # =================================================================

    def set_objective(self, objective):

        if self.solver == 'gurobi':
            self.model.setObjective(objective, grb.GRB.MAXIMIZE)
            self.model.update()

        if self.solver == 'pulp':
            self.problem.setObjective(objective)

        return self

    # Bipartite similarity
    # ~~~~~~~~~~~~~~~~~~~~

    def get_bipartite_similarity(
        self, items, otherItems, get_similarity
    ):
        """Bi-partite similarity: ∑  xij.pij
                                 i∈I
                                 j∈J
        """
        if self.solver == 'gurobi':

            objective, N = self._gurobi_get_bipartite_similarity(
                items, otherItems, get_similarity)

        if self.solver == 'pulp':

            objective, N = self._pulp_get_bipartite_similarity(
                items, otherItems, get_similarity)

        return objective, N

    def _pulp_get_bipartite_similarity(
        self, items, otherItems, get_similarity
    ):

        """Bi-partite similarity: ∑  xij.pij
                                 i∈I
                                 j∈J
        """

        values = [get_similarity(I, J)*self.x[I, J]
                  for I, J in itertools.product(items, otherItems)
                  if not np.isnan(get_similarity(I, J))]
        return sum(values), len(values)

    def _gurobi_get_bipartite_similarity(
        self, items, otherItems, get_similarity
    ):

        """Bi-partite similarity: ∑  xij.pij
                                 i∈I
                                 j∈J
        """

        values = [get_similarity(I, J)*self.x[I, J]
                  for I, J in itertools.product(items, otherItems)
                  if not np.isnan(get_similarity(I, J))]

        return grb.quicksum(values), len(values)

    # Bipartite dissimilarity
    # ~~~~~~~~~~~~~~~~~~~~~~~

    def get_bipartite_dissimilarity(
        self, items, otherItems, get_similarity
    ):

        """Bi-partite dissimilarity: ∑ (1-xij).(1-pij)
                                    i∈I
                                    j∈J
        """

        if self.solver == 'gurobi':

            objective, N = self._gurobi_get_bipartite_dissimilarity(
                items, otherItems, get_similarity)

        if self.solver == 'pulp':

            objective, N = self._pulp_get_bipartite_dissimilarity(
                items, otherItems, get_similarity)

        return objective, N

    def _pulp_get_bipartite_dissimilarity(
        self, items, otherItems, get_similarity
    ):
        """Bi-partite dissimilarity: ∑ (1-xij).(1-pij)
                                    i∈I
                                    j∈J
        """

        values = [(1-get_similarity(I, J))*(1-self.x[I, J])
                  for I, J in itertools.product(items, otherItems)
                  if not np.isnan(get_similarity(I, J))]
        return sum(values), len(values)

    def _gurobi_get_bipartite_dissimilarity(
        self, items, otherItems, get_similarity
    ):

        """Bi-partite dissimilarity: ∑ (1-xij).(1-pij)
                                    i∈I
                                    j∈J
        """

        values = [(1-get_similarity(I, J))*(1-self.x[I, J])
                  for I, J in itertools.product(items, otherItems)
                  if not np.isnan(get_similarity(I, J))]

        return grb.quicksum(values), len(values)

    def get_inter_cluster_dissimilarity(
        self, items, get_similarity
    ):

        """Inter-cluster dissimilarity:  ∑ (1-xij).(1-pij)
                                        i∈I
                                        j∈I
        """

        return self.get_bipartite_dissimilarity(
            items, items, get_similarity)

    def get_intra_cluster_similarity(
        self, items, get_similarity
    ):

        """Intra-cluster similarity: ∑  xij.pij
                                    i∈I
                                    j∈I
        """

        return self.get_bipartite_similarity(
            items, items, get_similarity)

    # =================================================================
    # SOLUTION
    # =================================================================

    def solve(self, **kwargs):

        if self.solver == 'gurobi':
            return self._gurobi_solve(**kwargs)

        if self.solver == 'pulp':
            return self._pulp_solve(**kwargs)

    def _pulp_solve(self, solver=None):

        """
        Solve ILP problem

        Parameters
        ----------
        solver :

        Returns
        -------
        solution : dict

        """

        self.problem.solve(solver=solver)

        # read solution
        solution = {}
        for key, variable in self.x.iteritems():
            solution[key] = variable.value()

        return solution

    def _gurobi_solve(
        self, init=None,
        method=None, mip_focus=None, heuristics=None,
        mip_gap=None, time_limit=None,
        threads=None, verbose=False
    ):

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

        return solution


# =====================================================================
# Objective functions
# =====================================================================

class InOutObjectiveMixin(object):

    """
    δ = argmax α ∑ δij.pij + (1-α) ∑ (1-δij).(1-pij)
                 i∈I                i∈I
                 j∈I                j∈I
    """

    def get_objective(self, items, get_similarity, alpha=0.5, **kwargs):
        """
        δ = argmax α ∑ δij.pij + (1-α) ∑ (1-δij).(1-pij)
                     i∈I                i∈I
                     j∈I                j∈I

        Parameters
        ----------
        items : list
            I
        get_similarity : func
            f(i, j) --> pij
        alpha : float, optional
            0 ≤ α ≤ 1. Defaults to 0.5
        """

        intra, N = self.get_intra_cluster_similarity(items, get_similarity)
        inter, _ = self.get_inter_cluster_dissimilarity(items, get_similarity)

        N = max(1, N)
        objective = 1./N*(alpha*intra+(1-alpha)*inter)

        return objective
