#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012-2014 Herve BREDIN (bredin@limsi.fr)

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

import ann
import mdtm
import seg
import repere
import trs
import xgtf
import etf
import tvm
import facetracks


class AnnotationParser(object):

    supported = {
        '.ann': ann.ANNParser,
        '.mdtm': mdtm.MDTMParser,
        '.seg': seg.SEGParser,
        '.repere': repere.REPEREParser,
        '.trs': trs.TRSParser,
        '.xgtf': xgtf.XGTFParser,
        '.facetracks': facetracks.FACETRACKSParser,
        '.etf0': etf.ETF0Parser,
        '.tvm': tvm.TVMParser,
    }

    @classmethod
    def guess(cls, path):
        import os
        _, extension = os.path.splitext(path)
        return AnnotationParser.supported.get(extension, None), extension

    def __init__(self, **kwargs):
        super(AnnotationParser, self).__init__()
        self.__parser = None
        self.__kwargs = kwargs

    def __get_uris(self):
        return self.__parser.uris
    uris = property(fget=__get_uris)

    def __get_modalities(self):
        return self.__parser.modalities
    modalities = property(fget=__get_modalities)

    def read(self, path, uri=None, modality=None, **kwargs):
        GuessParser, extension = self.__class__.guess(path)
        if GuessParser is None:
            raise NotImplementedError(
                "unsupported file format '%s'. supported: %s." %
                (extension, AnnotationParser.supported.keys()))
        if self.__parser is None or not isinstance(self.__parser, GuessParser):
            self.__parser = GuessParser(**self.__kwargs)
        self.__parser.read(path, uri=uri, modality=modality, **kwargs)
        return self

    def __call__(self, uri=None, modality=None, **kwargs):
        return self.__parser(uri=uri, modality=modality, **kwargs)
