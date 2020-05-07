#!/usr/bin/python3

import logging
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
from simtools.util import legendHandlers as legH

__all__ = ['readTelescopeLayout', 'plotArray']

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def plotArray(telescopes, rotateAngle):

    sizeFactor = 0
    hasSST = False
    telescopes['x'], telescopes['y'] = _rotate(rotateAngle,
                                               telescopes['x'],
                                               telescopes['y'])
    sizeFactor = max(np.max(telescopes['x']), np.max(telescopes['y']))/300.
    if any('SST' in telNameNow for telNameNow in telescopes['name']):
        hasSST = True

    patches = []
    for i_tel in range(len(telescopes)):
        patches.append(_getTelescopePatch(
            telescopes[i_tel]['name'][0:3],
            telescopes[i_tel]['x'],
            telescopes[i_tel]['y'],
            telescopes[i_tel]['radius']*sizeFactor)
        )

    plt.gca().add_collection(PatchCollection(patches, match_original=True))

    legendObjects = [legH.lstObject(), legH.mstObject()]
    legendLabels = ['LST', 'MST']
    legendHandlerMap = {legH.lstObject: legH.lstHandler(),
                        legH.mstObject: legH.mstHandler(),
                        legH.sstObject: legH.sstHandler()}
    if hasSST:
        legendObjects.append(legH.sstObject())
        legendLabels.append('SST')

    xTitle = 'x [m]'
    yTitle = 'y [m]'
    plt.axis('equal')
    plt.grid(True)
    plt.gca().set_axisbelow(True)
    plt.xlabel(xTitle, fontsize=18, labelpad=0)
    plt.ylabel(yTitle, fontsize=18, labelpad=0)
    plt.tick_params(axis='both', which='major', labelsize=15)

    plt.legend(legendObjects, legendLabels,
               handler_map=legendHandlerMap,
               prop={'size': 11}, loc='upper left')

    plt.tight_layout()

    return plt


def _getTelescopePatch(name, x, y, radius):

    colors = {'LST': 'darkorange', 'MST': 'dodgerblue', 'SST': 'black'}

    colorNow = colors[name]
    if name == 'LST':
        patch = mpatches.Circle((x, y),
                                radius=radius,
                                fill=False,
                                color=colorNow)
    elif name == 'MST':
        patch = mpatches.Rectangle((x - radius/2, y - radius/2),
                                   width=radius,
                                   height=radius,
                                   fill=True,
                                   color=colorNow)
    elif name == 'SST':
        patch = mpatches.Circle((x, y),
                                radius=radius,
                                fill=True,
                                color=colorNow)
    else:
        raise RuntimeError('Name of telescope unknown - {}'.format(name))

    return patch


def _rotate(rotationAngle, x, y):
    """
    Rotate x and y by the rotation angle given in rotationAngle.
    The function returns the rotated x and y values.
    Notice that rotationAngle must be given in degrees!
    """

    if not isinstance(x, type(y)):
        raise RuntimeError('x and y are not the same type! '
                           'Cannot perform transformation.')
    if not isinstance(x, list):
        xList, yList = _rotate(rotationAngle, [x], [y])
        return xList[0], yList[0]

    if len(x) != len(y):
        raise RuntimeError('Cannot perform coordinate transformation '
                           'when x and y have different lengths.')
    xTrans, yTrans = list(), list()
    rotateAngle = np.deg2rad(rotationAngle)

    for xNow, yNow in zip(x, y):
        xTrans.append(xNow*np.cos(rotateAngle) + yNow*np.sin(rotateAngle))
        yTrans.append((-1)*xNow*np.sin(rotateAngle) + yNow*np.cos(rotateAngle))

    return xTrans, yTrans


def readTelescopeLayout(fileName):

    headersType = {'names': ('x', 'y', 'radius', 'name'),
                   'formats': ('f8', 'f8', 'f8', 'U10')}

    telescopes = np.loadtxt(fileName, dtype=headersType, usecols=(5, 6, 8, 9))

    return telescopes
