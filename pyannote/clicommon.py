from argparse import ArgumentParser, SUPPRESS
from pyannote.parser import LSTParser, TimelineParser
import pyannote

parser = ArgumentParser(add_help=False)

parser.add_argument('--version', action='version', 
                       version=('PyAnnote %s' % pyannote.__version__))

parser.add_argument('--verbose', action='append_const', dest='verbose',
                    const=1, default=[], help='print progress information')

def uris_parser(path):
    return LSTParser().read(path)
parser.add_argument('--uris', type=uris_parser, metavar='uri.lst',
                       default=SUPPRESS, 
                       help='list of resources to process')

def uem_parser(path):
    return TimelineParser().read(path)
parser.add_argument('--uem', type=uem_parser, metavar='file.uem', 
                       default=SUPPRESS,
                       help='part of resources to process')

URIS = ["%s", "[URI]"]
"""List of allowed URI place-holders"""

def replaceURI(path, uri):
    """
    Replace URI place-holder
    
    Parameters
    ----------
    path : str
        Path with URI place-holder
    uri : str
        URI
    
    Returns
    -------
    new_path : str
        `path` with URI place-holder replaced by `uri`
    
    """
    new_path = str(path)
    for ph in URIS:
        new_path = new_path.replace(ph, uri)
    return new_path

def containsURI(path):
    """
    Check if path contains URI place-holder
    
    Parameters
    ----------
    path : str
        Path
        
    Returns
    -------
    contains : bool
        True if `path` contains one (or more) URI place-holders
        False otherwise
    
    """
    return any([path.find(ph) > -1 for ph in URIS])
