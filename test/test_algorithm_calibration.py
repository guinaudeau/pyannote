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

import numpy as np
import pyannote.algorithm.calibration.likelihood_ratio

class test_algorithm_calibration(object):

    def setup(self):
        pass

    def test_logLikelihoodRatioLinearRegression(self):
        n = 100000
        positive = np.random.randn(n) + 1
        negative = np.random.randn(n) - 1
        llrlr = pyannote.algorithm.calibration.likelihood_ratio.LogLikelihoodRatioLinearRegression()
        llrlr.fit(positive, negative)
        assert abs(llrlr.a - 2.) < 0.1
        assert abs(llrlr.b - 0.) < 0.1
