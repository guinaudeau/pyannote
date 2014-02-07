#!/usr/bin/env python
# encoding: utf-8

# Copyright 2013 Herve BREDIN (bredin@limsi.fr)

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

# =============================================================================
# IMPORTS
# =============================================================================
import pyannote.cli # common PyAnnote Command Line Interface

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================
argParser = pyannote.cli.initParser('Multimodal Probability Graphs (MPG)')

description = 'path to output file (pickled Networkx graph).' + pyannote.cli.URI_SUPPORT
argParser.add_argument('output', metavar='[URI].nxg', help=description,
                       type=OutputFileHandle())

description = 'add one vertex per speech turn in input SPEECH_TURNS file.'
argParser.add_argument('--s', metavar='SPEECH_TURNS', help=description,
                       type=InputGetAnnotation())

description = 'add edges between speech turns weighted according to SIMILARITY.'
argParser.add_argument('--ss', metavar='SIMILARITY', help=description,
                       type=InputGetSimilarity())


# =============================================================================
# ARGUMENT PARSING & POST-PROCESSING
# =============================================================================
try:
    args = argParser.parser_args()
except IOError as e:
    sys.stderr.write('%s' % e)
    sys.exit(-1)

# obtain list of resources
uris = pyannote.cli.get_uris()

# =============================================================================
# PROCESSING ONE RESOURCE AT A TIME
# =============================================================================
for u, uri in enumerate(uris):

    # inform the user about which resource is being processed
    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
        sys.stdout.flush()

    # create an empty multimodal probability graph
    G = MultimodalProbabilityGraph()


    # pickle final multimodal probability graph
    with args.output(uri=uri) as f:
        nx.write_gpickle(G, foutput)


