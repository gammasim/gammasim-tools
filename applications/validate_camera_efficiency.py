#!/usr/bin/python3

import logging
import matplotlib.pyplot as plt
import argparse

import simtools.util.general as gen
from simtools.model.telescope_model import TelescopeModel
from simtools.camera_efficiency import CameraEfficiency


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description=(
            'Calculate the camera efficiency of the telescope requested. '
            'Plot the camera efficiency vs wavelength for cherenkov and NSB light.'
        )
    )
    parser.add_argument(
        '-t',
        '--tel_type',
        help='Telescope type (e.g. mst-flashcam, lst)',
        type=str,
        required=True
    )
    parser.add_argument(
        '-l',
        '--label',
        help='Label (default=validate-camera-efficiency)',
        type=str,
        default='validate-camera-efficiency'
    )
    parser.add_argument(
        '-m',
        '--model_version',
        help='Model version (default=prod4)',
        type=str,
        default='prod4'
    )
    parser.add_argument(
        '-s',
        '--site',
        help='Site (default=South)',
        type=str,
        default='south'
    )
    parser.add_argument(
        '-v',
        '--verbosity',
        dest='logLevel',
        action='store',
        default='info',
        help='Log level to print (default is INFO)'
    )

    args = parser.parse_args()

    logger = logging.getLogger('validate_camera_efficiency')
    logger.setLevel(gen.getLogLevelFromUser(args.logLevel))

    telModel = TelescopeModel(
        telescopeType=args.tel_type,
        site=args.site,
        version=args.model_version,
        label=args.label,
        logger=logger.name
    )

    # For debugging purposes
    telModel.exportConfigFile()

    logger.info('Validating the camera efficiency of {}'.format(telModel.telescopeType))

    ce = CameraEfficiency(telescopeModel=telModel, logger=logger.name)
    ce.simulate(force=False)
    ce.analyze(force=True)

    # Plotting the camera efficiency for Cherenkov light
    plt = ce.plotCherenkovEfficiency()
    cherenkovPlotFile = 'cameraEfficiency-cherenkov-{}.pdf'.format(telModel.telescopeType)
    plt.savefig(cherenkovPlotFile, bbox_inches='tight')
    logger.info('Plotted cherenkov efficiency in {}'.format(cherenkovPlotFile))
    plt.clf()

    # Plotting the camera efficiency for NSB light
    plt = ce.plotNSBEfficiency()
    nsbPlotFile = 'cameraEfficiency-nsb-{}.pdf'.format(telModel.telescopeType)
    plt.savefig(nsbPlotFile, bbox_inches='tight')
    logger.info('Plotted NSB efficiency in {}'.format(nsbPlotFile))
    plt.clf()
