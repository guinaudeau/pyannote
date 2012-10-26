from argparse import ArgumentParser, SUPPRESS
from pyannote.parser import LSTParser, TimelineParser
import pyannote

parser = ArgumentParser(add_help=False)

parser.add_argument('--version', action='version', 
                       version=('PyAnnote %s' % pyannote.__version__))

parser.add_argument('--verbose', action='store_true',
                    help='print progress information')

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
def replaceURIS(path, uri):
    new_path = str(path)
    for ph in URIS:
        new_path = new_path.replace(ph, uri)
    return new_path

