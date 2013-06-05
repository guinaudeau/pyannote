from argparse import ArgumentParser, SUPPRESS
from pyannote.parser.lst import LSTParser
from pyannote.parser.timeline import TimelineParser
import pyannote

parser = ArgumentParser(add_help=False)

parser.add_argument('--version', action='version',
                       version=('PyAnnote %s' % pyannote.__version__))

parser.add_argument('--verbose', action='append_const', dest='verbose',
                    const=1, default=[], help='print progress information')



# --uri and --uris are mutually exclusive
# --uri is to process only one video
# --uris is to process a list of videos
uris = parser.add_mutually_exclusive_group()

def uri_parser(path):
    return [path]
uris.add_argument('--uri', type=uri_parser, metavar='URI',
                    dest='uris', default=SUPPRESS,
                    help='identifier of unique resource to process')

def uris_parser(path):
    return LSTParser().read(path)
uris.add_argument('--uris', type=uris_parser, metavar='uri.lst',
                  dest='uris', default=SUPPRESS,
                       help='list of resources to process')

def uem_parser(path):
    return TimelineParser().read(path)
parser.add_argument('--uem', type=uem_parser, metavar='file.uem',
                       default=SUPPRESS,
                       help='part of resources to process')

def msgURI():
    return " [URI] placeholder is replaced at processing time."

def replaceURI(path, uri):
    """
    Replace [URI] placeholder

    Parameters
    ----------
    path : str
        Path with [URI] placeholder
    uri : str
        URI

    Returns
    -------
    new_path : str
        `path` with [URI] placeholder replaced by `uri`

    """
    new_path = str(path)
    new_path = new_path.replace('[URI]', uri)
    return new_path

def containsURI(path):
    """
    Check if path contains [URI] placeholder

    Parameters
    ----------
    path : str
        Path

    Returns
    -------
    contains : bool
        True if `path` contains one (or more) [URI] placeholders
        False otherwise

    """
    return path.find('[URI]') > -1
