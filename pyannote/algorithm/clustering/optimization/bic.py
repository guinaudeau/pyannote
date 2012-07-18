from pyannote.algorithm.clustering.optimization.ilp import IntegerLinearProgramming
from pyannote.algorithm.clustering.model.gaussian import BICMMx

class BICILP(IntegerLinearProgramming, BICMMx):
    def __init__(self, penalty_coef=3.5, gurobi=True):
        super(BICILP, self).__init__(gurobi=gurobi, 
                                     penalty_coef=penalty_coef)

