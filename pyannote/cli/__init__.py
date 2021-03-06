#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012-2013 Herve BREDIN (bredin@limsi.fr)

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


from argparse import SUPPRESS
from pyannote.cli.uris import get_uris, URI_SUPPORT
from pyannote.cli.parent import initParser, parentArgumentParser

from pyannote.cli.argtypes import *

__all__ = [
    'SUPPRESS',
    'get_uris',
    'URI_SUPPORT',
    'initParser',
    'parentArgumentParser',
    'InputFileHandle',
    'OutputFileHandle',
    'InputList',
    'InputGetTimeline',
    'InputGetAnnotation',
    'InputGetAnnotationAndPath',
    'OutputWriteAnnotation',
]
