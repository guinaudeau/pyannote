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
import numpy as np
from progressbar import ProgressBar, Bar, ETA
from argparse import ArgumentParser, SUPPRESS
from pyannote import clicommon
argparser = ArgumentParser(parents=[clicommon.parser],
                           description='Statistics on annotations')

from pyannote.parser.annotation import AnnotationParser

argparser.add_argument('--modality', default=SUPPRESS, type=str,
                       help='modality to get stats from.')
def ann_parser(path):
    return (path, AnnotationParser().read(path))
argparser.add_argument('annotation', metavar='annotation', nargs='+',
                       type=ann_parser, help='path to annotations')

try:
    args = argparser.parse_args()
except Exception, e:
    sys.exit(e)

# get list of resources either from --uris option
# or from the set of provided annotations
if hasattr(args, 'uris'):
    uris = args.uris
else:
    uris = set([])
    for path, annotation in args.annotation:
        uris.update(annotation.uris)
    uris = sorted(uris)

# initialize matrices meant to store statistics
from pyannote.base.matrix import LabelMatrix
nlabels = LabelMatrix(dtype=int, default=0.)


pb = ProgressBar(widgets=[Bar(),' ', ETA()], term_width=80)
pb.maxval = len(uris)*len(args.annotation)
pb.start()

if hasattr(args, 'modality'):
    modality = args.modality
else:
    modality = None


for u, uri in enumerate(uris):

    if hasattr(args, 'uem'):
        uem = args.uem(uri)
    else:
        uem = None

    for h, (path, annotation) in enumerate(args.annotation):

        ann = annotation(uri, modality=modality)

        if uem is not None:
            ann = ann.crop(uem, mode='intersection')

        nlabels[uri, path] = len(ann.labels())

        pb.update(u*len(args.annotation)+h+1)

pb.finish()

# compute min, max, average
MINIMUM = '__ minimum __'
MAXIMUM = '__ maximum __'
GEOMEAN = '__ geomean __'
ARIMEAN = '__ arimean __'

import scipy.stats
for h, (path, _) in enumerate(args.annotation):
    nlabels[MINIMUM, path] = np.min(nlabels[set(uris), path].M)
    nlabels[MAXIMUM, path] = np.max(nlabels[set(uris), path].M)
    nlabels[GEOMEAN, path] = scipy.stats.gmean(nlabels[set(uris), path].M)
    nlabels[ARIMEAN, path] = np.mean(nlabels[set(uris), path].M)
print nlabels.to_table(title='# labels', factorize='C')


