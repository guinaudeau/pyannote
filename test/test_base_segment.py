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

from pyannote import Segment

class test_base_segment(object):

	def setup(self):
		self.s1 = Segment(start=1, end=3)
		self.s2 = Segment(start=2, end=4)
		self.s3 = Segment(start=3, end=5)
		self.s4 = Segment(start=4, end=6)
		self.s5 = Segment(start=5, end=7)

	def teardown(self):
		pass

	def test_precision(self):
		precision = 1e-6
		assert not Segment(start=1, end=1+precision)
		assert Segment(start=1, end=1+2*precision)

	def test_duration(self):
		assert self.s2.duration == 2

	def test_middle(self):
		assert self.s2.middle == 3

	def test_copy(self):
		s = self.s2.copy()
		assert self.s2 == s
		assert id(self.s2) != s

	def test_contains(self):
		s = Segment(start=2, end=6)
		assert not self.s1 in s
		assert self.s2 in s
		assert self.s3 in s
		assert self.s4 in s
		assert not self.s5 in s

	def test_and(self):
		assert self.s2 & self.s1 == Segment(start=2, end=3)
		assert self.s2 & self.s2 == Segment(start=2, end=4)
		assert self.s2 & self.s3 == Segment(start=3, end=4)
		assert not (self.s2 & self.s4)
		assert not (self.s2 & self.s5)

	def test_intersects(self):
		assert self.s2.intersects(self.s1)
		assert self.s2.intersects(self.s2)
		assert self.s2.intersects(self.s3)
		assert not self.s2.intersects(self.s4)
		assert not self.s2.intersects(self.s5)

	def test_overlaps(self):
		assert not self.s1.overlaps(5)
		assert not self.s2.overlaps(5)
		assert self.s3.overlaps(5)
		assert self.s4.overlaps(5)
		assert self.s5.overlaps(5)

	def test_or(self):
		assert self.s2 | self.s1 == Segment(start=1, end=4)
		assert self.s2 | self.s2 == Segment(start=2, end=4)
		assert self.s2 | self.s3 == Segment(start=2, end=5)
		assert self.s2 | self.s4 == Segment(start=2, end=6)
		assert self.s2 | self.s5 == Segment(start=2, end=7)

	def test_xor(self):
		assert not (self.s2 ^ self.s1)
		assert not (self.s2 ^ self.s2)
		assert not (self.s2 ^ self.s3)
		assert not (self.s2 ^ self.s4)
		assert self.s2 ^ self.s5 == Segment(start=4, end=5)

	def test_str(self):
		assert str(self.s1) == '[1.000 --> 3.000]'
		assert str(Segment(start=1.2345, end=5.6789)) == '[1.234 --> 5.679]'


