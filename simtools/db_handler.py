#!/usr/bin/python3

""" io_handler module """

import logging
from pathlib import Path
import datetime
import yaml

__all__ = ['getArrayDB']


def getArrayDB(databaseLocation):
    """ Return the dict with the array db info

    Args:
        databaseLocation (Path)

    Returns:
        dict: output Path

    """
    file = Path(databaseLocation).joinpath('arrays').joinpath('arrays.yml')
    out = dict()
    with open(file, 'r') as stream:
        out = yaml.load(stream, Loader=yaml.FullLoader)
    return out