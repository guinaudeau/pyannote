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
import pyannote.cli
from pyannote.algorithm.tagging import HungarianTagger, ArgMaxTagger, ConservativeDirectTagger
from pyannote.base.annotation import Unknown

argparser = pyannote.cli.initParser('Annotation tagging')

description = 'path to original annotation' + pyannote.cli.URI_SUPPORT
argparser.add_argument('input', metavar='original',
                       type=pyannote.cli.InputGetAnnotation(),
                       help=description)

description = 'path to annotation containing tags' + pyannote.cli.URI_SUPPORT
argparser.add_argument('names', metavar='tags',
                        type=pyannote.cli.InputGetAnnotation(),
                        help=description)

description = 'path to tagged annotation' + pyannote.cli.URI_SUPPORT
argparser.add_argument('output', metavar='tagged',
                       type=pyannote.cli.OutputWriteAnnotation(),
                       help=description)

mgroup = argparser.add_mutually_exclusive_group()

description = 'perform one name-to-one input label mapping'
mgroup.add_argument('--one-to-one', action='store_true', help=description)

description = 'perform one name-to-many input labels mapping'
mgroup.add_argument('--one-to-many', action='store_true', help=description)

description = 'perform direct segment tagging at the end'
argparser.add_argument('--segment', action='store_true',
                       help=description)


# Actual argument parsing
try:
    args = argparser.parse_args()
except IOError as e:
    sys.stderr.write('%s' % e)
    sys.exit(-1)


uris = pyannote.cli.get_uris()

if args.segment:
    segment_tagger = ConservativeDirectTagger()

if args.one_to_one:
    tagger = HungarianTagger()
elif args.one_to_many:
    tagger = ArgMaxTagger()



# only evaluate selection of uris
if hasattr(args, 'uris'):
    uris = args.uris
else:
    uris = args.input.uris

# process each URI, one after the other
for u, uri in enumerate(uris):

    # read input for current URI
    # and anonymize it
    original = args.input(uri).anonymize()

    # read names for current URI
    names = args.names(uri)

    # focus on UEM if provided
    if hasattr(args, 'uem'):
        uem = args.uem(uri)
        names = names.crop(uem, mode='intersection')

    tagged = tagger(names, original)
    if args.segment:
        tagged = segment_tagger(names, tagged)

    args.output(tagged)

