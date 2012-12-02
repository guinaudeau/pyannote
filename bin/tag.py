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

#!/usr/bin/env python
# encoding: utf-8

import sys
import pyannote
import numpy as np
from argparse import ArgumentParser, SUPPRESS
from progressbar import ProgressBar, Bar, ETA

from pyannote.parser import AnnotationParser, TimelineParser
from pyannote.parser import LSTParser, MDTMParser

from pyannote.base.matrix import Cooccurrence
from pyannote.algorithm.tagging import HungarianTagger, ArgMaxTagger

from pyannote import clicommon
argparser = ArgumentParser(parents=[clicommon.parser],
                           description='A tool for tagging of annotations')

def annotation_parser(path):
    return AnnotationParser().read(path)

def output_parser(path):
    return open(path, 'w')

argparser.add_argument('input', type=annotation_parser,
                       help='path to input annotation')

argparser.add_argument('names', type=annotation_parser,
                        help='path to name annotation')

argparser.add_argument('output', type=output_parser,
                        help='path to output')

mgroup = argparser.add_mutually_exclusive_group()

mgroup.add_argument('--one-to-one', action='store_true',
                    help='perform one name-to-one input label mapping')

mgroup.add_argument('--one-to-many', action='store_true',
                    help='perform one name-to-many input labels mapping')


# Actual argument parsing
args = argparser.parse_args()

# List of requested metrics
if args.one_to_one:
    tagger = HungarianTagger()

if args.one_to_many:
    tagger = ArgMaxTagger()

# only evaluate selection of uris
if hasattr(args, 'uris'):
    uris = args.uris
else:
    uris = args.input.uris

# process each URI, one after the other
for u, uri in enumerate(uris):
    
    # read input for current URI
    original = args.input(uri).anonymize()
    
    # read names for current URI
    names = args.names(uri)
    
    # focus on UEM if provided
    if hasattr(args, 'uem'):
        uem = args.uem(uri)
        names = names(uem, mode='intersection')
    
    tagged = tagger(names, original)
    
    MDTMParser().write(tagged, f=args.output)

args.output.close()
    
