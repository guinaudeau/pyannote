"""

Convert scores to calibrated log-likelihood ratios,
using negative and positive samples with linear :
	from llr import scores2llr
    llr = scores2llr(scores, negative, positive)

Direct call to the script outputs the calibrated llh ratios to stdout:
    python sc2llr.py negative.txt positive.txt < scores.txt > llr.txt
Additional values on the command line:
    - file for storing (a, b) linear mapping coefficients
    - number of bins for computing the transformation (default 15)

NB: uses density option for numpy.histogram() that appeared in numpy 1.6

"""

import numpy as np
if np.__version__ < '1.6':
    raise "Error: needs at least numpy version 1.6"
from scipy import stats
from scipy.stats import norm

def scores2llr(scores, negative, positive, nb=15, mapFile=''):
    """
    Convert scores to calibrated log-likelihood ratios,
    using a linear interpolation function trained with negative
    and positive sample scores
    
    Parameters:
    ----------
    scores : ndarray of scores for unknown samples
    negative : ndarray of scores for negative samples
    positive : ndarray of scores for positive samples
    nb : number of points for the linear interpolation function (def. 15)
    mapFile : file name for storing the mapping function
    
    Returns:
    -------
    ndarray of scores converted to log-likelihood ratios
    """
    map = computeLinearMapping(negative, positive, nb)
    if mapFile != '':
        np.savetxt(mapFile, map, '%g')
    return applyLinearMapping(scores, map)    

def computeMapping(negative, positive, nb=15):
    """
    Parameters:
    ----------
    negative : ndarray of scores for negative samples
    positive : ndarray of scores for positive samples
    nb : number of points for the linear interpolation function (def. 15)
    
    Returns:
    -------
    ndarray (2,nb) of interpolation function
    """
    # center analysis around means and std dev. of positive and negative samples
    m = (np.mean(negative) + np.mean(positive)) / 2
    s = np.max((np.std(negative), np.std(positive)))
    # bins are equally spaced into normal ppf of resulting normal distribution
    # keep -inf and +inf at bins boundaries so that the density is correctly normalized
    bins = norm.ppf(np.hstack((np.arange(0, 1, 1.0 / (nb + 2)), 1)), m, s)
    # empirical pdf estimation with histogram then convert to log domain
    (y0, x0) = np.histogram(negative, bins, density=True)
    (y1, x1) = np.histogram(positive, bins, density=True)
    # throw away boundaries 
    x = (bins[1:-2] + bins[2:-1]) / 2
    y0 = y0[1:-1]
    y1 = y1[1:-1]
    # check and remove remaining undefined values
    good = (y0 > 0) & (y1 > 0)
    x = x[good]
    y0 = y0[good]
    y1 = y1[good]
    # convert to log likelihood ratio
    y = np.log(y1) - np.log(y0)
    
    return np.vstack((x,y))

def applyMapping(scores, map):
    x,y = map
    # perform linear interpolation for converting scores to log likelihoods
    i = np.digitize(scores, x)
    # check out-of-boundaries
    i[i == 0] = 1
    i[i == len(x)] = len(x) - 1
    dx = x[i] - x[i - 1]
    dy = y[i] - y[i - 1]
    return y[i] + (scores - x[i]) * dy / dx

def computeLinearMapping(negative, positive, nb=15):
    x, y = computeMapping(negative, positive, nb)
    slope, intercept, r_value, p_value, slope_std_error = stats.linregress(x, y)
    return (slope, intercept)

def applyLinearMapping(scores, map):
    (a, b) = map
    return a * scores + b
    
# direct script execution
if __name__ == "__main__":
    import sys
    scores = np.loadtxt(sys.stdin)
    negative = np.loadtxt(sys.argv[1])
    positive = np.loadtxt(sys.argv[2])
    if len(sys.argv) > 3:
        mapfile = sys.argv[3]
    else:
        mapfile = ''
    if len(sys.argv) > 4:
        nb = int(sys.argv[4])
    else:
        nb = 15
    np.savetxt(sys.stdout, scores2llr(scores, negative, positive, nb, mapfile))
    
