#!/usr/bin/python3

import logging
import argparse
import matplotlib.pyplot as plt
from simtools import sites
import simtools.config as cfg
import simtools.io_handler as io

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-l',
        '--layout',
        help='Ecsv file with the hyper array layout', # TODO pick this up automatically
        type=str,
        required=True
    )
    parser.add_argument(
        '-s',
        '--sub_array',
        help='File with a list of telescope to select the sub-array.',
        type=str,
    )


    args = parser.parse_args()
    label = 'plot_array'

    # Output directory to save files related directly to this app
    outputDir = io.getApplicationOutputDirectory(cfg.get('outputLocation'), label)

    siteLabel = '{}'.format(args.layout.split('_')[-1].split('.')[0].capitalize())

    telescopes = sites.readTelescopeLayoutEcsv(args.layout)
    if args.sub_array is not None:
        telescopes = sites.selectSubArray(args.sub_array, telescopes)
        siteLabel = args.sub_array.split('CTA.')[1].split('.lis')[0].replace('.', '-')
    plt = sites.plotArray(telescopes, 270)
    plt.gca().set_title('{} telescope layout'.format(siteLabel),
                        fontsize=15, y=1.02)
    plotFile = outputDir.joinpath('{}-layout.pdf'.format(siteLabel))
    logger.info('Plotting in {}'.format(plotFile))
    plt.savefig(plotFile, format='pdf', bbox_inches='tight')
    plt.clf()
