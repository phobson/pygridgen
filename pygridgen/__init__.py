# encoding: utf-8
"""
PYGRIDGEN is a tool for building curvilinear grids.

PYGRIDGEN is based on Pavel Sakov's gridgen c-library, with python capabilities
added through ctypes.  There is also an interactive boundary creator that can be
used for making grids.

(c) Rob Hetland, 2012

Released under an MIT license.

"""


from .grid import *
from . import csa
from . import utils
from .tests import test, teststrict

__authors__ = [
    'Robert Hetland <hetland@tamu.edu>',
    'Rich Signell <rsignell@gmail.com',
    'Paul Hobson <phobson@geosyntec.com>'
]

__version__ = '0.3.dev'
