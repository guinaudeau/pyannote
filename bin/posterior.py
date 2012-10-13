#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012 Herve BREDIN (bredin@limsi.fr)

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


# Training mode
# 1. load reference segmentation
# 2. load clustering input segmentation
# 3. generate label clustering groundtruth matrix Y
# 4. generate label similarity matrix X
# 5. store X and Y

import sys
import pickle
import numpy as np
import pyannote
from argparse import ArgumentParser, SUPPRESS
from pyannote.parser import AnnotationParser, TimelineParser, LSTParser
from pyannote.parser import PLPParser
from pyannote.algorithm.clustering.util import label_clustering_groundtruth
from pyannote.algorithm.clustering.model.base import SimilarityMatrix
from pyannote.algorithm.clustering.model.gaussian import BICMMx

argparser = ArgumentParser(description='A tool for estimating the clustering posterior probability')
argparser.add_argument('--version', action='version', 
                       version=('PyAnnote %s' % pyannote.__version__))

def input_parser(path):
    return AnnotationParser().read(path)
def uem_parser(path):
    return TimelineParser().read(path)
def uris_parser(path):
    return LSTParser().read(path)

# First positional argument is reference segmentation file
# -- loaded at argument-parsing time by an instance of AnnotationParser
argparser.add_argument('reference', type=input_parser,
                       help='path to reference segmentation file')

# Second positional argument is input segmentation file
# -- loaded at argument-parsing time by an instance of AnnotationParser
argparser.add_argument('input', type=input_parser,
                       help='path to input segmentation file')

# Next positional argument is where to save parameters
argparser.add_argument('save', type=str, metavar='output',
                        help='path to output file')

# UEM file is loaded at argument-parsing time by an instance of TimelineParser
argparser.add_argument('--uem', type=uem_parser, 
                       help='path to Unpartitioned Evaluation Map (UEM) file')

# Training set -- loaded at argument-parsing time by an instance of LSTParser
argparser.add_argument('--uris', type=uris_parser, 
                       help='path to list used for training')

# BIC similarity
argparser.add_argument('--bic', action='store_true',
                       help='use BIC as similarity metric')

# BIC penalty coefficient
argparser.add_argument('--penalty', metavar='LAMBDA', type=float, default=3.5,
                       help='BIC penalty coefficient (default: 3.5)')

# Diagonal covariance matrix
argparser.add_argument('--diagonal', action='store_true', 
                       help='use diagonal covariance matrix (default: full)')

# PLP features
place_holders = ["%s", "[URI]"]
help_msg = "path to PLP feature file. the following URI placeholders are supported: %s." % " or ".join(place_holders[1:])
argparser.add_argument('--plp', type=str, help=help_msg, default=SUPPRESS)

# Verbosity switch
argparser.add_argument('--verbose', action='store_true',
                       help='print progress information')

# Actual argument parsing
args = argparser.parse_args()

data = {}

# In case of BIC similarity, make sure we got all needed parameters
if args.bic:
    covariance_type = 'diag' if args.diagonal else 'full'
    penalty_coef = args.penalty
    if not hasattr(args, 'plp'):
        sys.stderr.write('Needed --plp argument for BIC similarity')
        sys.exit()
    class Dummy(SimilarityMatrix, BICMMx):
        pass
    label_similarity_matrix = Dummy(penalty_coef=penalty_coef, 
                                    covariance_type=covariance_type)
    data['covariance_type'] = covariance_type
    data['penalty_coef'] = penalty_coef

X = np.empty((0,1))
Y = np.empty((0,1))

# Use a URI subset
if args.uris is not None:
    uris = args.uris
else:
    uris = args.reference.videos

for u, uri in enumerate(uris):
    
    # Verbosity
    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
        sys.stdout.flush()
    
    # reference segmentation
    reference = args.reference(uri)
    # input segmentation
    annotation = args.input(uri)
    
    # focus on UEM
    if args.uem is not None:
        uem = args.uem(uri)
        reference = reference(uem, mode='intersection')
        annotation = annotation(uem, mode='intersection')
    
    # get groundtruth
    y = label_clustering_groundtruth(reference, annotation)
    Y = np.append(Y, y.M)
    
    # get similarity 
    if args.bic:
        
        # PLP features
        path = args.plp
        for ph in place_holders:
            path = path.replace(ph, uri)
        feature = PLPParser().read(path)
        
        x = label_similarity_matrix(annotation, feature)
    
    X = np.append(X, x.M)

# save to output file
data['X'] = X
data['Y'] = Y
data['uris'] = uris
f = open(args.save, 'w')
pickle.dump(data, f)
f.close()
