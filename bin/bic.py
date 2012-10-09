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

import sys
import pyannote
from argparse import ArgumentParser, SUPPRESS
from pyannote.parser import AnnotationParser, TimelineParser, LSTParser
from pyannote.parser import PLPParser, MDTMParser
from pyannote.algorithm.clustering.agglomerative.bic import BICClustering
from pyannote.algorithm.clustering.agglomerative.bic import BICRecombiner

place_holders = ["%s", "[URI]"] 

argparser = ArgumentParser(description='A tool for BIC clustering')
argparser.add_argument('--version', action='version', 
                       version=('PyAnnote %s' % pyannote.__version__))

def input_parser(path):
    return AnnotationParser().read(path)
def output_parser(path):
    return open(path, 'w')
def uem_parser(path):
    return TimelineParser().read(path)
def uris_parser(path):
    return LSTParser().read(path)


# First positional argument is input segmentation file
# It is loaded at argument-parsing time by an instance of AnnotationParser
argparser.add_argument('input', type=input_parser, metavar='INPUT',
                       help='path to input segmentation file')

help_msg = "path to PLP feature file. the following URI placeholders are supported: %s." % " or ".join(place_holders[1:])
argparser.add_argument('plp', metavar='PLP', type=str, 
                       help=help_msg)

# Next positional argument is output segmentation file
# It is 'w'-opened at argument-parsing time
argparser.add_argument('output', type=output_parser, metavar='OUTPUT',
                        help='path to output of BIC clustering')

argparser.add_argument('--uris', type=uris_parser,
                       help='list of URI to process')

# UEM file is loaded at argument-parsing time by an instance of TimelineParser
argparser.add_argument('--uem', type=uem_parser, 
                       help='path to Unpartitioned Evaluation Map (UEM) file')

argparser.add_argument('--penalty', metavar='LAMBDA', type=float, default=3.5,
                       help='BIC penalty coefficient (default: 3.5) -- the smaller the coefficient, the purer the clusters')

argparser.add_argument('--diagonal', action='store_true', 
                       help='use diagonal covariance matrix (default: full)')

argparser.add_argument('--linear', 
        type=float, metavar='TOLERANCE', default=SUPPRESS,
        help='perform (linear) clustering of contiguous segments.')

argparser.add_argument('--verbose', action='store_true',
                       help='print progress information')

# Actual argument parsing
args = argparser.parse_args()

covariance_type = 'diag' if args.diagonal else 'full'
penalty_coef = args.penalty

if not hasattr(args, 'linear'):
    
    if args.verbose:
        msg = "BIC clustering [%s covariance, %g penalty coefficient]\n"
        sys.stdout.write(msg % (covariance_type, penalty_coef))
        sys.stdout.flush()
    
    bic = BICClustering(penalty_coef=penalty_coef,
                        covariance_type=covariance_type)
else:
    
    tolerance = float(args.linear)
    if args.verbose:
        msg = "Linear BIC clustering [%s covariance, %g penalty coefficient, " \
              "%gs tolerance]\n"
        sys.stdout.write(msg % (covariance_type, penalty_coef, tolerance))
        sys.stdout.flush()
    
    bic = BICRecombiner(penalty_coef=penalty_coef,
                        covariance_type=covariance_type,
                        tolerance=tolerance)


# only process selection of uris
if args.uris:
    uris = args.uris
else:
    uris = args.input.videos

# process each URI, one after the other
for u, uri in enumerate(uris):
    
    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
        sys.stdout.flush()
    
    # input annotation
    annotation = args.input(uri)
    
    # focus on UEM
    if args.uem is not None:
        uem = args.uem(uri)
        annotation = annotation(uem, mode='intersection')
    
    # PLP features
    path = args.plp
    for ph in place_holders:
        path = path.replace(ph, uri)
    feature = PLPParser().read(path)
    
    # actual BIC clustering
    output = bic(annotation, feature)
    
    # save to file
    MDTMParser().write(output, f=args.output)

# close output file
args.output.close()