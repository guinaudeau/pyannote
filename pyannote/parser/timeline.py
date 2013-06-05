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

import uem


class TimelineParser(object):

    supported = {
        '.uem': uem.UEMParser,
    }

    def __guess(self, extension):
        return TimelineParser.supported.get(extension, None)

    def __init__(self):
        super(TimelineParser, self).__init__()
        self.__parser = None

    def __get_uris(self):
        return self.__parser.uris
    uris = property(fget=__get_uris)

    def read(self, path, uri=None, **kwargs):
        import os
        _, extension = os.path.splitext(path)
        GuessParser = self.__guess(extension)
        if GuessParser is None:
            raise NotImplementedError(
                "unsupported file format '%s'. supported: %s." %
                (extension, TimelineParser.supported.keys()))
        if self.__parser is None or not isinstance(self.__parser, GuessParser):
            self.__parser = GuessParser()
        self.__parser.read(path, uri=uri, **kwargs)
        return self

    def __call__(self, uri=None, **kwargs):
        return self.__parser(uri=uri, **kwargs)
