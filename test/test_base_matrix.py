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

from pyannote import Segment, Annotation
from pyannote import LabelMatrix

class test_base_matrix(object):

	def setup(self):
		pass
		# self.source = Annotation(uri='uri', modality='source')
		# self.source[Segment(0.0, 1.0), '_'] = 'a'
		# self.source[Segment(1.0, 3.0), '_'] = 'b'
		# self.source[Segment(2.2, 3.0), '_'] = 'c'

		# self.target = Annotation(uri='uri', modality='target')
		# self.target[Segment(0.0, 1.0), '_'] = 'A'
		# self.target[Segment(1.0, 2.0), '_'] = 'B'
		# self.target[Segment(2.0, 2.5), '_'] = 'C'


	def teardown(self):
		pass

	def test_shape(self):
		m = LabelMatrix(rows=[1,2,3,4], columns=[1,2])
		assert m.shape == (4, 2)



