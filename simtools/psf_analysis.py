'''
Module to analise psf images (e.g. results from ray tracing simulations).
Main functionalities are: computing centroids, psf containers etc.

Author: Raul R Prado

'''

import logging
from math import sqrt, fabs, pi

import matplotlib.pyplot as plt
import numpy as np

from simtools.util.general import collectKwargs, setDefaultKwargs


__all__ = ['PSFImage']


class PSFImage:
    '''
    Image composed of list of photon positions (2D).

    Load photon list from sim_telarray file and compute centroids, psf containers, effective area,
    as well as plot the image as a 2D histogram.
    Internal units: photon positions in cm internally.

    Parameters
    ----------
    focalLenght: float
        Focal length of the system in cm, needed to convert quantities from cm to deg. If None,
        getPSF will only work in cm (not in deg).

    Atributtes
    ----------
    effectiveArea: float
        Mirror effective area in cm.

    Methods
    -------
    readSimtelFile(file)
        Read a photon list produced by sim_telarray.
    getPSF(fraction=0.8, unit='cm')
        Compute and return a PSF container.
    getEffecticeArea()
        Return effective area under the condition that total area was set given.
    plotImage(**kwargs)
        Plot image as a 2D histogram
    plotIntegral(**kwargs)
        Plot cumulative intensity as a function containing fraction.
    '''
    def __init__(self, focalLength=None, totalScatteredArea=None, logger=__name__):
        '''
        Parameters
        ----------
        focalLength: float, optional
            Focal length of the system in cm. If not given, PSF can only be computed in cm.
        totalScatteredArea: float, optional
            Scatter area of all photons in cm^2. If not given, effective area cannot be computed.
        logger: str
            Logger name to use in this instance
        '''

        self._logger = logging.getLogger(logger)
        self.photonPosX = list()
        self.photonPosY = list()
        self.centroidX = None
        self.centroidY = None
        self._totalArea = totalScatteredArea
        self._storedPSF = dict()
        if focalLength is not None:
            self._cmToDeg = 180. / pi / focalLength
            self._hasFocalLength = True
        else:
            self._hasFocalLength = False

    def readSimtelFile(self, file):
        '''
        Read photon list file generated by sim_telarray and store the photon positions (2D).

        Parameters
        ----------
        file: str
            Name of sim_telarray file with photon list.

        Raises
        ------
        RuntimeError
            If photon positions X and Y are not compatible or are empty.

        '''
        self._logger.info('Reading SimtelFile {}'.format(file))
        self._totalPhotons = 0
        with open(file, 'r') as f:
            for line in f:
                self._processSimtelLine(line)

        if not self._isPhotonPositionsOK():
            msg = 'Problems reading Simtel file - invalid data'
            self._logger.error(msg)
            raise RuntimeError(msg)

        self.centroidX = np.mean(self.photonPosX)
        self.centroidY = np.mean(self.photonPosY)
        self._numberOfDetectedPhotons = len(self.photonPosX)
        self._effectiveArea = self._numberOfDetectedPhotons * self._totalArea / self._totalPhotons

    def _isPhotonPositionsOK(self):
        '''
        Verify if the photon positions are ok.

        Returns
        -------
        bool
            True if photon positions are ok, False if they are not.
        '''
        cond1 = len(self.photonPosX) != 0
        cond2 = len(self.photonPosY) != 0
        cond3 = len(self.photonPosX) == len(self.photonPosY)
        return cond1 and cond2 and cond3

    def _processSimtelLine(self, line):
        '''
        Supporting function to readSimtelFile.

        Parameters
        ----------
        line: str
            A line from the photon list file generated by sim_telarray.
        '''
        words = line.split()
        if 'falling on an area of' in line:
            self._totalPhotons += int(words[4])
            totalAreaInFile = float(words[14])
            if self._totalArea is None:
                self._totalArea = totalAreaInFile
            elif totalAreaInFile != self._totalArea:
                self._logger.warning(
                    'Conflicting value of the total area found'
                    ' {} != {}'.format(self._totalArea, totalAreaInFile) +
                    ' - Keeping the original value'
                )
            else:
                # Do nothing - Keep the original value of _totalArea
                pass
        elif '#' in line or len(words) == 0:
            # Skipping comments
            pass
        else:
            # Storing photon position from cols 2 and 3
            self.photonPosX.append(float(words[2]))
            self.photonPosY.append(float(words[3]))

    def getEffectiveArea(self):
        '''
        Return effective area pre calculated

        Returns
        -------
        float
            Pre-calculated effective area. None if it could not be calculated (e.g because the total
            scattering area was not set).
        '''
        if '_effectiveArea' in self.__dict__ and self._effectiveArea is not None:
            return self._effectiveArea
        else:
            self._logger.error('Effective Area could not be calculated')
            return None

    def setEffectiveArea(self, value):
        '''
        Set effective area

        Parameters
        ----------
        value: float
            Effective area

        '''
        self._effectiveArea = value

    def getPSF(self, fraction=0.8, unit='cm'):
        '''
        Return PSF

        Parameters
        ----------
        fraction: float
            Fraction of photons within the containing radius.
        unit: str
            'cm' or 'deg'. 'deg' will not work if focal length was not set.

        Returns
        -------
        float:
            Containing diameter for a certain intensity fraction (PSF).

        '''
        if unit == 'deg' and not self._hasFocalLength:
            self._logger.error('PSF cannot be computed in deg because focal length is not set')
            return None
        if fraction not in self._storedPSF.keys():
            self._computePSF(fraction)
        unitFactor = 1 if unit == 'cm' else self._cmToDeg
        return self._storedPSF[fraction] * unitFactor

    def setPSF(self, value, fraction=0.8, unit='cm'):
        '''
        Set PSF calculated from other methods

        Parameters
        ----------
        value: float
            PSF value to be set
        fraction: float
            Fraction of photons within the containing radius.
        unit: str
            'cm' or 'deg'. 'deg' will not work if focal length was not set.
        '''
        if unit == 'deg' and not self._hasFocalLength:
            self._logger.error('PSF cannot be set in deg because focal length is not set')
            return
        unitFactor = 1 if unit == 'cm' else 1. / self._cmToDeg
        self._storedPSF[fraction] = value * unitFactor

    def _computePSF(self, fraction):
        '''
        Compute and store PSF.

        Parameters
        ----------
        fraction: float
            Fraction of photons within the containing radius
        '''
        self._storedPSF[fraction] = self._findPSF(fraction)

    def _findPSF(self, fraction):
        '''
        Try to find PSF by a smart algorithm first. If it fails, _findRadiusByScanning is called and
        do it by brute force.

        Parameters
        ----------
        fraction: float
            Fraction of photons within the containing radius.

        Returns
        -------
        float:
            Diameter of the circular container with a certain fraction of the photons.

        '''
        self._logger.debug('Finding PSF for fraction = {}'.format(fraction))

        xPosSq = [i**2 for i in self.photonPosX]
        yPosSq = [i**2 for i in self.photonPosY]
        xPosSig = sqrt(np.mean(xPosSq) - self.centroidX**2)
        yPosSig = sqrt(np.mean(yPosSq) - self.centroidY**2)
        radiusSig = sqrt(xPosSig**2 + yPosSig**2)

        targetNumber = fraction * self._numberOfDetectedPhotons
        currentRadius = 1.5 * radiusSig
        startNumber = self._sumPhotonsInRadius(currentRadius)
        SCALE = 0.5 * sqrt(currentRadius * currentRadius / startNumber)
        deltaNumber = startNumber - targetNumber
        nIter = 0
        MAX_ITER = 100
        TOLERANCE = self._numberOfDetectedPhotons / 1000.
        foundRadius = False
        while not foundRadius and nIter < MAX_ITER:
            nIter += 1
            dr = -deltaNumber * SCALE / sqrt(targetNumber)
            while currentRadius + dr < 0:
                dr *= 0.5
            currentRadius += dr
            currentNumber = self._sumPhotonsInRadius(currentRadius)
            deltaNumber = currentNumber - targetNumber
            foundRadius = fabs(deltaNumber) < TOLERANCE

        if foundRadius:
            # Diameter = 2 * radius
            return 2 * currentRadius
        else:
            self._logger.warning('Could not find PSF efficiently - trying by scanning')
            return self._findRadiusByScanning(targetNumber, radiusSig)

    def _findRadiusByScanning(self, targetNumber, radiusSig):
        '''
        Find radius by scanning, aka brute force.

        Parameters
        ----------
        targetNumber: float
            Number of photons inside the diameter to be found.
        radiusSig: float
            Sigma of the radius to be used as scale.

        Returns
        -------
        float:
            Radius of the circle with targetNumber photons inside.
        '''
        self._logger.debug('Finding PSF by scanning')

        def scan(dr, radMin, radMax):
            '''
            Scan the image from radMin to radMax uin steps of dr ntil it finds targetNumber photons
            inside.

            Returns
            -------
            (float, float, float):
                Average radius, min radius, max radius of the interval where targetNumber photons
                are inside.
            '''
            r0, r1 = radMin, radMin + dr
            s0, s1 = 0, 0
            foundRadius = False
            while not foundRadius:
                s0, s1 = self._sumPhotonsInRadius(r0), self._sumPhotonsInRadius(r1)
                if s0 < targetNumber and s1 > targetNumber:
                    foundRadius = True
                    break
                if r1 > radMax:
                    break
                r0 += dr
                r1 += dr
            if foundRadius:
                return (r0 + r1) / 2, r0, r1
            else:
                self._logger.error('Could not find PSF by scanning')
                raise RuntimeError

        # Run scan few times with smaller dr to optimize search.
        # Step 0
        radius, radMin, radMax = scan(0.1*radiusSig, 0, 4*radiusSig)
        # Step 1
        radius, radMin, radMax = scan(0.005*radiusSig, radMin, radMax)
        return radius

    def _sumPhotonsInRadius(self, radius):
        ''' Return the number of photons inside a certain radius. '''
        nPhotons = 0
        for xx, yy in zip(self.photonPosX, self.photonPosY):
            rr2 = (xx - self.centroidX)**2 + (yy - self.centroidY)**2
            nPhotons += 1 if rr2 < radius**2 else 0
        return nPhotons

    def getImageData(self, centralized=True):
        '''
        Provide image data (2D photon positions in cm) as lists.

        Parameters
        ----------
        centralized: bool
            Centroid of the image is set to (0, 0) if True.

        Returns
        -------
        (x, y), the photons positions in cm.
        '''
        if centralized:
            xPosData = (np.array(self.photonPosX) - self.centroidX)
            yPosData = (np.array(self.photonPosY) - self.centroidY)
        else:
            xPosData = np.array(self.photonPosX)
            yPosData = np.array(self.photonPosY)
        dType = {
            'names': ('X', 'Y'),
            'formats': ('f8', 'f8')
        }
        return np.core.records.fromarrays(np.c_[xPosData, yPosData].T, dtype=dType)

    def plotImage(self, centralized=True, **kwargs):
        '''
        Plot 2D image as histogram (in cm).

        Parameters
        ----------
        centralized: bool
            Centroid of the image is set to (0, 0) if True.
        **kwargs:
            image_* for the histogram plot and psf_* for the psf circle.
        '''
        data = self.getImageData(centralized)

        kwargs = setDefaultKwargs(
            kwargs,
            image_bins=80,
            image_cmap=plt.cm.gist_heat_r,
            psf_color='k',
            psf_fill=False,
            psf_lw=2,
            psf_ls='--'
        )
        kwargsForImage = collectKwargs('image', kwargs)
        kwargsForPSF = collectKwargs('psf', kwargs)

        ax = plt.gca()
        # Image histogram
        ax.hist2d(data['X'], data['Y'], **kwargsForImage)

        # PSF circle
        center = (0, 0) if centralized else (self.centroidX, self.centroidY)
        circle = plt.Circle((0, 0), self.getPSF(0.8) / 2, **kwargsForPSF)
        ax.add_artist(circle)

    def getCumulativeData(self):
        '''
        Provide cumulative data (intensity vs radius).

        Returns
        -------
        (radius, intensity)
        '''
        radiusAll = list(np.linspace(0, 1.6 * self.getPSF(0.8), 30))
        intensity = list()
        for rad in radiusAll:
            intensity.append(self._sumPhotonsInRadius(rad) / self._numberOfDetectedPhotons)
        dType = {
            'names': ('Radius [cm]', 'Relative intensity'),
            'formats': ('f8', 'f8')
        }
        return np.core.records.fromarrays(np.c_[radiusAll, intensity].T, dtype=dType)

    def plotCumulative(self, **kwargs):
        ''' Plot cumulative data (intensity vs radius). '''
        data = self.getCumulativeData()
        plt.plot(data['Radius [cm]'], data['Relative intensity'], **kwargs)


# end of PSFImage
