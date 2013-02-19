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

from argparse import ArgumentParser, SUPPRESS
from pyannote.cli.argtypes import InputGetTimeline
from pyannote.cli import URI_SUPPORT, URIHandler
from pyannote.parser import LSTParser
import pyannote

def parentArgumentParser(version=True, verbose=True, uri=True, uem=True):
    """
    Create a new parent argument parser
    
    Parameters
    ----------
    version : bool, optional
        Add --version option
    verbose : bool, optional
        Add --verbose option
    uri : bool, optional
        Add --uri and --uris options
    uem : bool, optional
        Add --uem option
    
    Returns
    -------
    parser : ArgumentParser
        Argument parser with predefined common options
    
    """
    
    # create empty argument parser
    parser = ArgumentParser(add_help=False)
    
    # version option (--version)
    if version:
        parser.add_argument('--version', action='version', 
                            version=('PyAnnote %s' % pyannote.__version__))
    
    # verbosity option (--verbose)
    if verbose:
        description = 'increment verbosity level.'
        parser.add_argument('--verbose', dest='verbose',
                            action='append_const', const=1, default=[], 
                            help=description)
    
    # uri filtering exclusive options (--uri xor --uris)
    if uri:
        uris = parser.add_mutually_exclusive_group()
        
        # Option --uri
        def uri_unique(u):
            URIHandler().addFromFilter([u])
            return [u]
        
        description = 'identifier of unique resource to process.'
        uris.add_argument('--uri', dest='uris', metavar='URI', 
                          type=uri_unique, default=SUPPRESS,
                          help=description)
        
        # Option --uris
        def uris_from_file(path):
            uris = LSTParser().read(path)
            URIHandler().addFromFilter(uris)
            return uris
        
        description = 'path to list of resources to process.'        
        uris.add_argument('--uris', dest='uris', metavar='uri.lst',
                          type=uris_from_file, default=SUPPRESS, 
                          help=description)
    
    # uem filtering option (--uem)
    if uem:
        description = 'path to file containing part of resources to process.' + URI_SUPPORT
        parser.add_argument('--uem', dest='uem', metavar='file.uem',
                            type=InputGetTimeline(), default=SUPPRESS,
                            help=description)
    
    return parser

def initParser(description, version=True, verbose=True, uri=True, uem=True):
    """
    Parameters
    ----------
    description : str
        Description of command line tool
    version : bool, optional
        Add --version option
    verbose : bool, optional
        Add --verbose option
    uri : bool, optional
        Add --uri and --uris options
    uem : bool, optional
        Add --uem option
    
    Returns
    -------
    parser : ArgumentParser
        Argument parser with predefined common options
    """
    parent = parentArgumentParser(version=version, verbose=verbose, uri=uri, uem=uem)
    parser = ArgumentParser(parents=[parent], description=description)
    return parser
