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

import sys
import os.path
import pyannote.cli.uris
from pyannote.parser import TimelineParser, AnnotationParser, LSTParser, LabelMatrixParser


class InputFileHandle(object):

    def __init__(self):
        super(InputFileHandle, self).__init__()

    def __call__(self, path):

        if pyannote.cli.uris.contains_uri(path):

            def getFileHandle(uri=None):

                # replace placeholder
                rpath = pyannote.cli.uris.replace_uri(path, uri)

                return open(rpath, 'r')

        else:

            def getFileHandle(uri=None):

                if path == '-':
                    return sys.stdin
                else:
                    return open(path, 'r')

        return getFileHandle


class InputGetTimeline(object):

    def __init__(self, initArgs=None):
        """
        Parameters
        ----------
        initArgs : dict, optional
            Keyword arguments passed when initializing timeline file parser
        """
        super(InputGetTimeline, self).__init__()
        self.initArgs = {} if initArgs is None else initArgs
        # self.parser = TimelineParser(**(self.initArgs))

    def __call__(self, path):

        # initialize parser
        self.parser = TimelineParser(**(self.initArgs))

        # there is one timeline file per resource
        if pyannote.cli.uris.contains_uri(path):

            def getTimeline(uri):
                # replace placeholder
                rpath = pyannote.cli.uris.replace_uri(path, uri)
                # read file
                self.parser.read(rpath, uri=uri)
                # return annotation
                return self.parser(uri=uri)

        # there is one big file containing timelines for all resources
        else:

            # read file
            self.parser.read(path)

            # add uris to global set of available resources
            pyannote.cli.uris.add_input_uris(self.parser.uris)

            def getTimeline(uri):
                return self.parser(uri=uri)

        return getTimeline


class InputGetAnnotation(object):

    def __init__(self, initArgs=None):
        """
        Parameters
        ----------
        initArgs : dict, optional
            Keyword arguments passed when initializing annotation file parser
        """
        super(InputGetAnnotation, self).__init__()
        self.initArgs = {} if initArgs is None else initArgs
        # self.parser = AnnotationParser(**(self.initArgs))

    def __call__(self, path):

        # initialize parser
        self.parser = AnnotationParser(**(self.initArgs))

        # there is one annotation file per resource
        if pyannote.cli.uris.contains_uri(path):

            def getAnnotation(uri=None, modality=None):
                # replace placeholder
                rpath = pyannote.cli.uris.replace_uri(path, uri)
                # read file
                self.parser.read(rpath, uri=uri, modality=modality)
                # return annotation
                return self.parser(uri=uri, modality=modality)

        # there is one big file containing annotations for all resources
        else:

            # read file
            self.parser.read(path)

            # add uris to global set of available resources
            pyannote.cli.uris.add_input_uris(self.parser.uris)

            getAnnotation = self.parser
            # def getAnnotation(uri=None, modality=None):
            #     return self.parser(uri=uri, modality=modality)

        return getAnnotation


class InputGetAnnotationAndPath(InputGetAnnotation):
    def __call__(self, path):
        return (path, super(InputGetAnnotationAndPath, self).__call__(path))


class InputList(object):

    def __init__(self, initArgs=None):
        super(InputList, self).__init__()
        self.initArgs = {} if initArgs is None else initArgs
        self.parser = LSTParser(**(self.initArgs))

    def __call__(self, path):
        """
        Parameters
        ----------
        path : str
            Path to list file

        Returns
        -------
        lines : list
            List of strings (one per line in file)
        """
        return self.parser.read(path)


class InputGetMatrix(object):

    def __init__(self, initArgs=None):
        """
        Parameters
        ----------
        initArgs : dict, optional
            Keyword arguments passed when initializing matrix parser
        """
        super(InputGetMatrix, self).__init__()
        self.initArgs = {} if initArgs is None else initArgs

    def __call__(self, path):

        # initialize parser
        self.parser = LabelMatrixParser(**(self.initArgs))

        # there is one annotation file per resource
        if pyannote.cli.uris.contains_uri(path):

            def getMatrix(uri=None, modality=None):
                # replace placeholder
                rpath = pyannote.cli.uris.replace_uri(path, uri)
                # read file and return matrix
                return self.parser.read(rpath)

        # there is one big file containing matrices for all resources
        else:
            raise IOError('')

        return getMatrix


class OutputFileHandle(object):

    def __init__(self):
        super(OutputFileHandle, self).__init__()

    def __call__(self, path):

        if pyannote.cli.uris.contains_uri(path):

            def getFileHandle(uri=None):

                # replace placeholder
                rpath = pyannote.cli.uris.replace_uri(path, uri)

                # check if we are about to overwrite a file
                if os.path.isfile(rpath):
                    raise IOError('File %s already exists.' % rpath)

                return open(rpath, 'w')

        else:

            def getFileHandle(uri=None):

                if path == '-':
                    return sys.stdout
                else:
                    if os.path.isfile(path):
                        raise IOError('File %s already exists.' % path)
                    return open(path, 'w')

        return getFileHandle


class OutputWriteAnnotation(object):

    def __init__(self, initArgs=None):
        super(OutputWriteAnnotation, self).__init__()
        self.initArgs = {} if initArgs is None else initArgs

    def __call__(self, path):

        if pyannote.cli.uris.contains_uri(path):

            def writeAnnotation(annotation):

                # replace placeholder
                uri = annotation.uri
                if not uri:
                    raise IOError('ERROR: no URI available to replace placeholder in path to output file.')
                rpath = pyannote.cli.uris.replace_uri(path, uri)

                # check if we are about to overwrite a file
                if os.path.isfile(rpath):
                    raise IOError('File %s already exists.' % rpath)

                # create parser based on rpath extension
                Parser, extension = AnnotationParser.guess(rpath)
                parser = Parser(**(self.initArgs))

                # create file and write annotation
                with open(rpath, 'w') as f:
                    parser.write(annotation, f=f)

        else:

            # check if we are about to overwrite a file
            if os.path.isfile(path):
                raise IOError('File %s already exists.\n' % path)

            # create parser based on path extension
            Parser, extension = AnnotationParser.guess(path)
            parser = Parser(**(self.initArgs))

            def writeAnnotation(annotation):

                # open file and append annotation at the end
                with open(path, 'a') as f:
                    parser.write(annotation, f=f)

        return writeAnnotation
