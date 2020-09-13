'''
Camera Efficiency simulations and analysis.

Author: Raul R Prado
'''

import logging
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path
from collections import defaultdict
import re

import astropy.units as u
from astropy.io import ascii
from astropy.table import Table

import simtools.config as cfg
import simtools.io_handler as io
from simtools import visualize
from simtools.util import names
from simtools.util.general import collectArguments
from simtools.util.model import getCameraName
from simtools.model.telescope_model import TelescopeModel
from simtools.model.model_parameters import CAMERA_RADIUS_CURV

__all__ = ['CameraEfficiency']


class CameraEfficiency:
    '''
    Class for handling camera efficiency simulations and analysis.

    Attributes
    ----------
    label: str
        Instance label.

    Methods
    -------
    simulate(force=False)
        Simulate camera efficiency using testeff from sim_telarray.
    analyse(export=True, force=False)
        Analyze output from testeff and store results in _results.
    exportResults()
        Export results to a csv file.
    plot(key, **kwargs)
        Plot key vs wavelength, where key may be cherenkov or nsb.
    '''
    ALL_INPUTS = {'zenithAngle': {'default': 20, 'unit': u.deg}}

    def __init__(
        self,
        telescopeModel,
        label=None,
        simtelSourcePath=None,
        filesLocation=None,
        logger=__name__,
        **kwargs
    ):
        '''
        CameraEfficiency init.

        Parameters
        ----------
        telescopeModel: TelescopeModel
            Instance of the TelescopeModel class.
        label: str
            Instance label, optional.
        simtelSourcePath: str (or Path), optional.
            Location of sim_telarray installation. If not given, it will be taken from the
            config.yml file.
        filesLocation: str (or Path), optional.
            Parent location of the output files created by this class. If not given, it will be
            taken from the config.yml file.
        logger: str
            Logger name to use in this instance
        **kwargs:
            Physical parameters with units (if applicable). Options: zenithAngle (default 20 deg).
        '''
        self._logger = logging.getLogger(logger)

        self._simtelSourcePath = Path(cfg.getConfigArg('simtelPath', simtelSourcePath))
        self._filesLocation = cfg.getConfigArg('outputLocation', filesLocation)
        self._telescopeModel = self._validateTelescopeModel(telescopeModel)
        self.label = label if label is not None else self._telescopeModel.label

        self._baseDirectory = io.getCameraEfficiencyOutputDirectory(self._filesLocation, self.label)
        self._baseDirectory.mkdir(parents=True, exist_ok=True)

        self._hasResults = False

        collectArguments(self, args=['zenithAngle'], allInputs=self.ALL_INPUTS, **kwargs)

        self._loadFiles()
    # END of init

    def __repr__(self):
        return 'CameraEfficiency(label={})\n'.format(self.label)

    def _validateTelescopeModel(self, tel):
        ''' Validate TelescopeModel

        Parameters
        ----------

        tel: TelescopeModel
            An assumed instance of the TelescopeModel class.
        '''
        if isinstance(tel, TelescopeModel):
            self._logger.debug('TelescopeModel OK')
            return tel
        else:
            msg = 'Invalid TelescopeModel'
            self._logger.error(msg)
            raise ValueError(msg)

    def _loadFiles(self):
        ''' Define the variables for the file names, including the results, simtel and log file. '''
        # Results file
        fileNameResults = names.cameraEfficiencyResultsFileName(
                self._telescopeModel.telescopeName,
                self._zenithAngle,
                self.label
        )
        self._fileResults = self._baseDirectory.joinpath(fileNameResults)
        # SimtelOutput file
        fileNameSimtel = names.cameraEfficiencySimtelFileName(
                self._telescopeModel.telescopeName,
                self._zenithAngle,
                self.label
        )
        self._fileSimtel = self._baseDirectory.joinpath(fileNameSimtel)
        # Log file
        fileNameLog = names.cameraEfficiencyLogFileName(
                self._telescopeModel.telescopeName,
                self._zenithAngle,
                self.label
        )
        self._fileLog = self._baseDirectory.joinpath(fileNameLog)

    def simulate(self, force=False):
        '''
        Simulate camera efficiency using testeff.

        Parameters
        ----------
        force: bool
            Force flag will remove existing files and simulate again.
        '''
        self._logger.info('Simulating CameraEfficiency')

        if self._fileSimtel.exists() and not force:
            self._logger.info('Simtel file exists and force=False - skipping simulation')
            return

        # Processing camera pixel features
        pixelShape = self._telescopeModel.camera.getPixelShape()
        pixelShapeCmd = '-hpix' if pixelShape in [1, 3] else '-spix'
        pixelDiameter = self._telescopeModel.camera.getPixelDiameter()

        # Processing focal length
        focalLength = self._telescopeModel.getParameter('effective_focal_length')
        if focalLength == 0.:
            self._logger.warning('Using focal_lenght because effective_focal_length is 0')
            focalLength = self._telescopeModel.getParameter('focal_length')

        # Processing mirror class
        mirrorClass = 1
        if self._telescopeModel.hasParameter('mirror_class'):
            mirrorClass = self._telescopeModel.getParameter('mirror_class')

        # Processing camera transmission
        cameraTransmission = 1
        if self._telescopeModel.hasParameter('camera_transmission'):
            cameraTransmission = self._telescopeModel.getParameter('camera_transmission')

        # Processing camera filter
        # A special case is needed for recent ASTRI models because testeff does not
        # support 2D camera filters
        cameraFilterFile = self._telescopeModel.getParameter('camera_filter')
        if self._telescopeModel.isASTRI() and self._telescopeModel.isFile2D('camera_filter'):
            self._logger.warning(
                'Camera filter file is being replaced by transmission_astri_window_average.dat'
                ' because testeff does not support 2D camera filters.'
            )
            cameraFilterFile = 'transmission_astri_window_average.dat'

        # Processing mirror reflectivity
        # A special case is needed for recent ASTRI models because testeff does not
        # support 2D mirror reflectivity
        mirrorReflectivity = self._telescopeModel.getParameter('mirror_reflectivity')
        if self._telescopeModel.isASTRI() and self._telescopeModel.isFile2D('mirror_reflectivity'):
            self._logger.warning(
                'Mirror reflectivity (and secondary) file is being replaced by'
                ' ref_astri_2017-06_T0.dat because testeff does not support 2D files.'
            )
            mirrorReflectivity = 'ref_astri_2017-06_T0.dat'

        # Camera name
        cameraName = getCameraName(self._telescopeModel.telescopeName)

        # cmd -> Command to be run at the shell
        cmd = str(self._simtelSourcePath.joinpath('sim_telarray/bin/testeff'))
        cmd += ' -nm -nsb-extra'
        cmd += ' -alt {}'.format(self._telescopeModel.getParameter('altitude'))
        cmd += ' -fatm {}'.format(self._telescopeModel.getParameter('atmospheric_transmission'))
        cmd += ' -flen {}'.format(focalLength * 0.01)  # focal lenght in meters
        cmd += ' -fcur {}'.format(CAMERA_RADIUS_CURV[cameraName])
        cmd += ' {} {}'.format(pixelShapeCmd, pixelDiameter)
        if mirrorClass == 1:
            cmd += ' -fmir {}'.format(self._telescopeModel.getParameter('mirror_list'))
        cmd += ' -fref {}'.format(mirrorReflectivity)
        if mirrorClass == 2:
            cmd += ' -m2'
        cmd += ' -teltrans {}'.format(self._telescopeModel.getTelescopeTransmissionParameters()[0])
        cmd += ' -camtrans {}'.format(cameraTransmission)
        cmd += ' -fflt {}'.format(cameraFilterFile)
        cmd += ' -fang {}'.format(
            self._telescopeModel.camera.getLightguideEfficiencyAngleFileName()
        )
        cmd += ' -fwl {}'.format(
            self._telescopeModel.camera.getLightguideEfficiencyWavelengthFileName()
        )
        cmd += ' -fqe {}'.format(self._telescopeModel.getParameter('quantum_efficiency'))
        cmd += ' {} {}'.format(200, 1000)  # lmin and lmax
        cmd += ' {} 1 {}'.format(300, self._zenithAngle)  # Xmax, ioatm, zenith angle
        cmd += ' 2>{}'.format(self._fileLog)
        cmd += ' >{}'.format(self._fileSimtel)

        # Moving to sim_telarray directory before running
        cmd = 'cd {} && {}'.format(self._simtelSourcePath.joinpath('sim_telarray'), cmd)

        self._logger.info('Running sim_telarray with cmd: {}'.format(cmd))
        os.system(cmd)
        return
    # END of simulate

    def analyze(self, export=True, force=False):
        '''
        Analyze camera efficiency output file and store the results in _results.

        Parameters
        ----------
        export: bool
            If True, results will be exported to a file automatically. Alternatively, exportResults
            function can be used.
        force: bool
            If True, existing results files will be removed and analysis will be done again.
        '''
        self._logger.info('Analyzing CameraEfficiency')

        if self._fileResults.exists() and not force:
            self._logger.info('Results file exists and force=False - skipping analyze')
            self._readResults()
            return

        # List of parameters to be calculated and stored
        effPars = [
            'wl',
            'eff',
            'effAtm',
            'qe',
            'ref',
            'masts',
            'filt',
            'pixel',
            'atmTrans',
            'cher',
            'nsb',
            'atmCorr',
            'nsbSite',
            'nsbSiteEff',
            'nsbBe',
            'nsbBeEff',
            'C1',
            'C2',
            'C3',
            'C4',
            'C4x',
            'N1',
            'N2',
            'N3',
            'N4',
            'N4x'
        ]

        _results = defaultdict(list)

        # Search for at least 5 consecutive numbers to see that we are in the table
        re_table = re.compile('{0}{0}{0}{0}{0}'.format(r'[-+]?[0-9]*\.?[0-9]+\s+'))
        with open(self._fileSimtel, 'r') as file:
            for line in file:
                if re_table.match(line):
                    words = line.split()
                    numbers = [float(w) for w in words]
                    for i in range(len(effPars) - 10):
                        _results[effPars[i]].append(numbers[i])
                    C1 = numbers[8] * (400 / numbers[0])**2
                    C2 = C1 * numbers[4] * numbers[5]
                    C3 = C2 * numbers[6] * numbers[7]
                    C4 = C3 * numbers[3]
                    C4x = C1 * numbers[3] * numbers[6] * numbers[7]
                    _results['C1'].append(C1)
                    _results['C2'].append(C2)
                    _results['C3'].append(C3)
                    _results['C4'].append(C4)
                    _results['C4x'].append(C4x)
                    N1 = numbers[14]
                    N2 = N1 * numbers[4] * numbers[5]
                    N3 = N2 * numbers[6] * numbers[7]
                    N4 = N3 * numbers[3]
                    N4x = N1 * numbers[3] * numbers[6] * numbers[7]
                    _results['N1'].append(N1)
                    _results['N2'].append(N2)
                    _results['N3'].append(N3)
                    _results['N4'].append(N4)
                    _results['N4x'].append(N4x)

        self._results = Table(_results)
        self._hasResults = True

        print('\33[40;37;1m')
        self._logger.info('Spectrum weighted reflectivity: {}'.format(self.calcReflectivity()))
        self._logger.info(
            'Camera nominal efficiency with gaps (B-TEL-1170): {}'.format(
                self.calcCameraEfficiency()
            )
        )
        self._logger.info(
            'Telescope total efficiency with gaps (was A-PERF-2020): {}'.format(
                self.calcTelEfficiency()
            )
        )
        self._logger.info(
            'Total telescope Cherenkov light eff./sqrt(NSB total eff.) '
            '(A-PERF-2025/B-TEL-0090): {}'.format(
                self.calcTotEfficiency(self.calcTelEfficiency())
            )
        )
        print('\033[0m')

        if export:
            self.exportResults()
    # END of analyze

    def exportResults(self):
        ''' Export results to a csv file. '''
        if not self._hasResults:
            self._logger.error('Cannot export results because they do not exist')
        else:
            self._logger.info('Exporting results to {}'.format(self._fileResults))
            ascii.write(self._results, self._fileResults, format='basic', overwrite=True)

    def _readResults(self):
        ''' Read existing results file and store it in _results. '''
        table = ascii.read(self._fileResults, format='basic')
        self._results = table
        self._hasResults = True

    def calcTelEfficiency(self):
        '''
        Calculate the telescope total efficiency including gaps (as defined in A-PERF-2020).
        '''

        # Sum(C1) from 300 - 550 nm:
        c1ReducedWL = self._results['C1'][
            [wlNow > 299 and wlNow < 551 for wlNow in self._results['wl']]
        ]
        c1Sum = np.sum(c1ReducedWL)
        # Sum(C4) from 200 - 999 nm:
        c4Sum = np.sum(self._results['C4'])
        mastsFactor = self._results['masts'][0]
        fillFactor = self._telescopeModel.camera.getCameraFillFactor()

        telEffeciency = fillFactor*(c4Sum/(mastsFactor*c1Sum))

        return telEffeciency

    def calcCameraEfficiency(self):
        '''
        Calculate the camera nominal efficiency including gaps (as defined in B-TEL-1170).
        '''

        # Sum(C1) from 300 - 550 nm:
        c1ReducedWL = self._results['C1'][
            [wlNow > 299 and wlNow < 551 for wlNow in self._results['wl']]
        ]
        c1Sum = np.sum(c1ReducedWL)
        # Sum(C4x) from 300 - 550 nm:
        c4xReducedWL = self._results['C4x'][
            [wlNow > 299 and wlNow < 551 for wlNow in self._results['wl']]
        ]
        c4xSum = np.sum(c4xReducedWL)
        fillFactor = self._telescopeModel.camera.getCameraFillFactor()

        camEffeciencyNoGaps = c4xSum/c1Sum
        camEffeciency = camEffeciencyNoGaps*fillFactor

        return camEffeciency

    def calcTotEfficiency(self, telEffeciency):
        '''
        Calculate the telescope total efficiency including gaps (as defined in A-PERF-2020).

        Parameters
        ----------
        telEffeciency: float
            The telescope efficiency as calculated by calcTelEfficiency()
        '''

        # Sum(N1) from 300 - 550 nm:
        n1ReducedWL = self._results['N1'][
            [wlNow > 299 and wlNow < 551 for wlNow in self._results['wl']]
        ]
        n1Sum = np.sum(n1ReducedWL)
        # Sum(N4) from 200 - 999 nm:
        n4Sum = np.sum(self._results['N4'])
        mastsFactor = self._results['masts'][0]
        fillFactor = self._telescopeModel.camera.getCameraFillFactor()

        telEffeciencyNSB = fillFactor*(n4Sum/(mastsFactor*n1Sum))

        return telEffeciency/np.sqrt(telEffeciencyNSB)

    def calcReflectivity(self):
        '''
        Calculate the Cherenkov spectrum weighted reflectivity in the range 300-550 nm.
        '''

        # Sum(C1) from 300 - 550 nm:
        c1ReducedWL = self._results['C1'][
            [wlNow > 299 and wlNow < 551 for wlNow in self._results['wl']]
        ]
        c1Sum = np.sum(c1ReducedWL)
        # Sum(C2) from 300 - 550 nm:
        c2ReducedWL = self._results['C2'][
            [wlNow > 299 and wlNow < 551 for wlNow in self._results['wl']]
        ]
        c2Sum = np.sum(c2ReducedWL)

        return c2Sum/c1Sum/self._results['masts'][0]

    def plot(self, key, **kwargs):
        '''
        Plot key vs wavelength.

        Parameters
        ----------
        key: str
            cherenkov or nsb
        **kwargs:
            kwargs for plt.plot

        Raises
        ------
        KeyError
            If key is not among the valid options.
        '''
        if key not in ['cherenkov', 'nsb']:
            msg = 'Invalid key to plot'
            self._logger.error(msg)
            raise KeyError(msg)

        ax = plt.gca()
        firstLetter = 'C' if key == 'cherenkov' else 'N'
        for par in ['1', '2', '3', '4', '4x']:
            ax.plot(
                self._results['wl'],
                self._results[firstLetter + par],
                label=firstLetter + par,
                **kwargs
            )

    def plotCherenkovEfficiency(self):
        '''
        Plot cherenkov efficiency vc wavelength.

        Returns
        -------
        plt
        '''
        self._logger.info('Plotting cherenkov efficiency vs wavelength')

        columnTitles = {
            'wl': 'Wavelength [nm]',
            'C1': r'C1: Cherenkov light on ground',
            'C2': r'C2: C1 $\times$ ref. $\times$ masts',
            'C3': r'C3: C2 $\times$ filter $\times$ lightguide',
            'C4': r'C4: C3 $\times$ q.e.',
            'C4x': r'C4x: C1 $\times$ filter $\times$ lightguide $\times$ q.e.'
        }

        tableToPlot = Table([self._results[colNow] for colNow in columnTitles.keys()])

        for columnNow, columnTitle in columnTitles.items():
            tableToPlot.rename_column(columnNow, columnTitle)

        plt = visualize.plotTable(
            tableToPlot,
            yTitle='Cherenkov light efficiency',
            title='{} response to Cherenkov light'.format(self._telescopeModel.telescopeName),
            noMarkers=True
        )

        return plt

    def plotNSBEfficiency(self):
        '''
        Plot NSB efficiency vc wavelength.

        Returns
        -------
        plt
        '''
        self._logger.info('Plotting NSB efficiency vs wavelength')
        columnTitles = {
            'wl': 'Wavelength [nm]',
            'N1': r'N1: NSB light on ground (B\&E)',
            'N2': r'N2: N1 $\times$ ref. $\times$ masts',
            'N3': r'N3: N2 $\times$ filter $\times$ lightguide',
            'N4': r'N4: N3 $\times$ q.e.',
            'N4x': r'N4x: N1 $\times$ filter $\times$ lightguide $\times$ q.e.'
        }

        tableToPlot = Table([self._results[colNow] for colNow in columnTitles.keys()])

        for columnNow, columnTitle in columnTitles.items():
            tableToPlot.rename_column(columnNow, columnTitle)

        plt = visualize.plotTable(
            tableToPlot,
            yTitle='Nightsky background light efficiency',
            title='{} response to nightsky background light'.format(
                self._telescopeModel.telescopeName
            ),
            noMarkers=True
        )

        plt.gca().set_yscale('log')
        ylim = plt.gca().get_ylim()
        plt.gca().set_ylim(1e-3, ylim[1])

        return plt
# END of CameraEfficiency
