#!/usr/bin/python3

import logging
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
from astropy import units as u
from astropy.table import QTable
from simtools.util import legendHandlers as legH

__all__ = ['readTelescopeLayoutEcsv', 'readTelescopeLayoutCorsika', 'plotArray']

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def plotArray(telescopes, rotateAngle):

    sizeFactor = 0
    hasSST = False
    if rotateAngle != 0:
        telescopes['pos_x'], telescopes['pos_y'] = _rotate(rotateAngle,
                                                   telescopes['pos_x'],
                                                   telescopes['pos_y'])
    sizeFactor = max(np.max(telescopes['pos_x']), np.max(telescopes['pos_y']))/(300.*u.m) 
    fontsize = 12
    if any('S' in telNameNow for telNameNow in telescopes['telescope_name']):
        hasSST = True
        fontsize = 5

    patches = []
    for i_tel in range(len(telescopes)):
        patches.append(_getTelescopePatch(
            telescopes[i_tel]['telescope_name'][0],
            telescopes[i_tel]['pos_x'],
            telescopes[i_tel]['pos_y'],
            telescopes[i_tel]['radius']*sizeFactor)
        )
        plt.text(
            telescopes[i_tel]['pos_x'].value, 
            telescopes[i_tel]['pos_y'].value + telescopes[i_tel]['radius'].value, 
            telescopes[i_tel]['telescope_name'],
            horizontalalignment='center',
            verticalalignment='bottom',
            fontsize=fontsize
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

    colors = {'L': 'darkorange', 'M': 'dodgerblue', 'S': 'black'}

    colorNow = colors[name]
    if 'L' == name:
        patch = mpatches.Circle(
            (x.value, y.value),
            radius=radius.value,
            fill=False,
            color=colorNow
        )
    elif 'M' == name:
        patch = mpatches.Rectangle(
            ((x - radius/2).value, (y - radius/2).value),
            width=radius.value,
            height=radius.value,
            fill=True,
            color=colorNow
        )
    elif 'S' == name:
        patch = mpatches.Circle(
            (x.value, y.value),
            radius=radius.value,
            fill=True,
            color=colorNow
        )
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


def readTelescopeLayoutCorsika(fileName):

    # FIXME Adding the Ecsv option below broke this function.
    # It is probably not necessary anyway anymore, so it will stay broken
    # until a good reason to fix it is found.

    headersType = {'names': ('pos_x', 'pos_y', 'radius', 'telescope_name'),
                   'formats': ('f8', 'f8', 'f8', 'U10')}

    telescopes = np.loadtxt(fileName, dtype=headersType, usecols=(5, 6, 8, 9))

    return telescopes


def readTelescopeLayoutEcsv(fileName):

    telNameDict = {'L': 'LST', 'M': 'MST', 'S': 'SST'}
    telescopes = QTable.read(fileName)
    telescopes['radius'] = [
        float(
            telescopes.meta['corsika_sphere_radius'][telNameDict[telNameNow[0]]].split()[0]
        ) for telNameNow in telescopes['telescope_name']
    ]
    telescopes['radius'].unit = u.Unit(telescopes.meta['corsika_sphere_radius']['LST'].split()[1])

    return telescopes


def selectSubArray(fileName, hyperArray):
    
    subArray = np.loadtxt(fileName, dtype=('U10'), usecols=(4))
    telescopes = hyperArray[[telNow in subArray for telNow in hyperArray['telescope_name']]]

    return telescopes
