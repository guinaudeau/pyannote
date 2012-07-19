from pyannote.algorithm.clustering.optimization.ilp import IntegerLinearProgramming
from pyannote.algorithm.clustering.model.gaussian import BICMMx

class BICILP(IntegerLinearProgramming, BICMMx):
    def __init__(self, penalty_coef=3.5):
        super(BICILP, self).__init__(penalty_coef=penalty_coef)

