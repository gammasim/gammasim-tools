#!/usr/bin/python3

import logging
import matplotlib.pyplot as plt
from simtools import sites
import simtools.config as cfg

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


if __name__ == '__main__':

    telescopes = sites.readTelescopeLayout(cfg.findFile('LaPalma_coords.lis'))
    plt = sites.plotArray(telescopes, 270)
    plt.gca().set_title('La Palma telescope layout',
                        fontsize=15, y=1.02)
    plt.savefig('LaPalmaLayout.pdf', format='pdf', bbox_inches='tight')
    plt.clf()

    telescopes = sites.readTelescopeLayout(cfg.findFile('Paranal_coords.lis'))
    plt = sites.plotArray(telescopes, 270)
    plt.gca().set_title('Paranal telescope layout',
                        fontsize=15, y=1.02)
    plt.savefig('ParanalLayout.pdf', format='pdf', bbox_inches='tight')
    plt.clf()
