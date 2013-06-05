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

import tvt


class LabelMatrixParser(object):

    specific = {
        # '.mat': METRICMATParser,
        '.tvt': tvt.TVTParser,
    }

    @classmethod
    def guess(cls, path):
        import os
        _, extension = os.path.splitext(path)
        return LabelMatrixParser.specific.get(extension, None), extension

    def __init__(self):
        super(LabelMatrixParser, self).__init__()
        self.__parser = None

    def read(self, path, **kwargs):

        GuessParser, extension = self.__class__.guess(path)

        if GuessParser is None:
            import pickle
            f = open(path, 'r')
            matrix = pickle.load(f)
            f.close()
        else:
            if self.__parser is None or not isinstance(self.__parser,
                                                       GuessParser):
                self.__parser = GuessParser(**kwargs)
            matrix = self.__parser.read(path, **kwargs)
        return matrix
