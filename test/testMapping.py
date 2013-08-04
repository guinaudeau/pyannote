from pyannote import Segment, Annotation
from pyannote.algorithm.mapping import ConservativeDirectMapper
from pyannote.algorithm.mapping import ArgMaxMapper
from pyannote.algorithm.mapping import HungarianMapper


class test_algo_mapping(object):

	def setup(self):

		#   |  A   B   C
		# --+-------------
		# a | 1.0 0.0 0.0
		# b | 0.0 1.0 0.5
		# c | 0.0 0.0 0.3

		self.source = Annotation(uri='uri', modality='source')
		self.source[Segment(0.0, 1.0), '_'] = 'a'
		self.source[Segment(1.0, 3.0), '_'] = 'b'
		self.source[Segment(2.2, 3.0), '_'] = 'c'

		self.target = Annotation(uri='uri', modality='target')
		self.target[Segment(0.0, 1.0), '_'] = 'A'
		self.target[Segment(1.0, 2.0), '_'] = 'B'
		self.target[Segment(2.0, 2.5), '_'] = 'C'

	def teardown(self):
		pass

	def test_conservative_direct_mapper(self):
		cdm = ConservativeDirectMapper()

		mapping = cdm(self.source, self.target)
		assert set(mapping['a']) == set(['A'])
		assert set(mapping['b']) == set([])
		assert set(mapping['c']) == set(['C'])

		mapping = cdm(self.target, self.source)
		assert set(mapping['A']) == set(['a'])
		assert set(mapping['B']) == set(['b'])
		assert set(mapping['C']) == set([])

	def test_argmax_mapper(self):
		amm = ArgMaxMapper()

		mapping = amm(self.source, self.target)
		assert set(mapping['a']) == set(['A'])
		assert set(mapping['b']) == set(['B'])
		assert set(mapping['c']) == set(['C'])

		mapping = amm(self.target, self.source)
		assert set(mapping['A']) == set(['a'])
		assert set(mapping['B']) == set(['b'])
		assert set(mapping['C']) == set(['b'])

	def test_hungarian_mapper(self):
		hm = HungarianMapper()

		mapping = hm(self.source, self.target)
		assert set(mapping['a']) == set(['A'])
		assert set(mapping['b']) == set(['B'])
		assert set(mapping['c']) == set(['C'])

		mapping = hm(self.target, self.source)
		assert set(mapping['A']) == set(['a'])
		assert set(mapping['B']) == set(['b'])
		assert set(mapping['C']) == set(['c'])

