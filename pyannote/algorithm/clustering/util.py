import scipy.stats
import numpy as np

def _estimate_label_duration_distribution(annotations, law, floc, fscale):
    durations = np.empty((0,))
    for A in annotations:
        D = A._timeline.duration()
        d = np.array([A.label_duration(L) for L in A.labels()])
        d /= D
        durations = np.concatenate((durations, d), axis=0)
    params = law.fit(durations, floc=floc, fscale=fscale)
    return params

def estimate_prior_probability(annotations, law=scipy.stats.beta, floc=None, fscale=None):
    """Estimate clustering prior probability based on distribution of label durations
    
    Parameters
    ----------
    annotations : list of :class:`pyannote.Annotation`
        Groundtruth annotations.
    law : scipy.stats.rv_continuous, optional
        How to model distribution of label durations.
        Defaults to scipy.stats.beta
        
    Returns
    -------
    prior : float
        Clustering prior probability
    """
    params = _estimate_label_duration_distribution(annotations, law, floc, fscale)
    prior = law.expect(lambda d: d*d, args=params)
    return prior


from pyannote.algorithm.mapping import ConservativeDirectMapper
from pyannote.base.mapping import ManyToOneMapping
from pyannote.base.matrix import LabelMatrix

def _get_pn_scores(clustering, R, H, F):
    mapper = ConservativeDirectMapper()
    mapping = ManyToOneMapping.fromMapping(mapper(H, R))
    # remove all labels with no found mapping
    _mapping = mapping.empty()
    for l, r in mapping:
        if r:
            _mapping += (l, r)
    mapping = _mapping
    
    # C[i, j] = True iff labels i & j should be in the same cluster
    C = LabelMatrix(dtype=bool, default=False)
    for labels, _ in mapping:
        for i in labels:
            for j in labels:
                C[i, j] = True
    
    if not C:
        return np.empty((0,)), np.empty((0,))
    
    # Get clustering scores (and sort them according to C)
    # (visualization should show clusters as blocks on the diagonal)
    clustering.start(H, F)
    scores = clustering.imx_matrix[set(C.labels[0]), set(C.labels[0])]
    n = scores.M[np.where(C.M == False)]
    p = scores.M[np.where(C.M == True)]
    
    return p, n

def estimate_likelihood_ratio(uris, get_ref, get_hyp, get_features, clustering):
    """
    
    Parameters
    ----------
    uris : list
        List of URIs to use for estimation
    get_ref : func
        get_ref(uri) = reference
    get_hyp : func
        get_hyp(uri) = hypothesis
    get_features : func
        get_features(uri) = features
    clustering : 
        Clustering algorithm
    
    Returns
    -------
    llr : func
        Function that returns likelihood ratio p(t | H) / p(t | ~H)
        t ==> p(t | H) / p(t | ~H)
    """
    
    negatives = np.empty((0,))
    positives = np.empty((0,))
    mapper = ConservativeDirectMapper()
    
    for u, uri in enumerate(uris):
        
        R = get_ref(uri)
        H = get_hyp(uri)
        F = get_features(uri)
        p, n = _get_pn_scores(clustering, R, H, F)
        negatives = np.concatenate((negatives, n), axis=0)
        positives = np.concatenate((positives, p), axis=0)
    
    max_min = max(np.min(positives), np.min(negatives))
    min_max = min(np.max(positives), np.max(positives))
    p_kde = scipy.stats.gaussian_kde(positives)
    n_kde = scipy.stats.gaussian_kde(negatives)
    
    def lr(t):
        is_scalar = False
        if np.isscalar(t):
            is_scalar = True
            t = np.array([t])
        else:
            is_scalar = False
            t = np.asarray(t)
        
        shape = t.shape
        t = t.reshape((1, -1))
        
        p_t = p_kde(t)
        n_t = n_kde(t)
        
        T = (p_t / n_t).reshape((1,-1))
        
        undefined_low = t < max_min
        undefined_high = t > min_max
        T[np.where(undefined_low)] = 0.
        T[np.where(undefined_high)] = np.inf
        
        if is_scalar:
            T = T[0, 0]
        else:
            T = T.reshape(shape)
        return T
    
    return lr
