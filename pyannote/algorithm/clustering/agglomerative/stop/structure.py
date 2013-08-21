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

from base import BaseStoppingCriterionMixin


class NumberOfClustersSMx(BaseStoppingCriterionMixin):
    """

    Parameters
    ----------
    num_clusters : int

    """
    def smx_setup(self, num_clusters=1., **kwargs):
        self.smx_num_clusters = num_clusters

    def smx_stop(self, status):
        return len(self.annotation.labels()) < self.smx_num_clusters
