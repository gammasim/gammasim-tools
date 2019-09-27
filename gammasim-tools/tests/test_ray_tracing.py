#!/usr/bin/python3

import logging
import matplotlib.pyplot as plt
import numpy as np
from copy import copy

from ctamclib.ray_tracing import RayTracing
from ctamclib.telescope_model import TelescopeModel

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.DEBUG)

yamlDBPath = (
    '/home/prado/Work/Projects/CTA_MC/svn/Simulations/MCModelDescription/trunk/configReports'
)
simtelPath = (
    '/afs/ifh.de/group/cta/scratch/prado/corsika_simtelarray/corsika6.9_simtelarray_19-03-08'
)


def test_ssts(show=False):
    # Test with 3 SSTs
    sourceDistance = 10
    site = 'south'
    version = 'prod4'
    zenithAngle = 20
    offAxisAngle = [0, 4.0]

    telTypes = ['sst-1m', 'sst-astri', 'sst-gct']
    telModels = list()
    rayTracing = list()
    for t in telTypes:
        tel = TelescopeModel(
            yamlDBPath=yamlDBPath,
            telescopeType=t,
            site=site,
            version=version,
            label='test-sst'
        )
        telModels.append(t)

        ray = RayTracing(
            simtelSourcePath=simtelPath,
            telescopeModel=tel,
            sourceDistance=sourceDistance,
            zenithAngle=zenithAngle,
            offAxisAngle=offAxisAngle
        )
        ray.simulate(test=True, force=True)
        ray.analyze(force=True)

        rayTracing.append(ray)

    # Plotting

    plt.figure(figsize=(8, 6), tight_layout=True)
    ax = plt.gca()
    ax.set_xlabel('off-axis')
    ax.set_ylabel('d80')

    for ray in rayTracing:
        ray.plot('d80_deg', marker='o', linestyle=':')

    if show:
        plt.show()


def test_rx(show=False):
    sourceDistance = 10
    site = 'south'
    version = 'prod4'
    label = 'test-astri'
    zenithAngle = 20
    offAxisAngle = [0, 2.5, 5.0]

    tel = TelescopeModel(
        yamlDBPath=yamlDBPath,
        telescopeType='astri',
        site=site,
        version=version,
        label=label
    )

    ray = RayTracing(
        simtelSourcePath=simtelPath,
        telescopeModel=tel,
        sourceDistance=sourceDistance,
        zenithAngle=zenithAngle,
        offAxisAngle=offAxisAngle
    )

    ray.simulate(test=True, force=True)
    ray_rx = copy(ray)

    ray.analyze(force=True)
    ray_rx.analyze(force=True, useRX=True)

    # Plotting PSF images
    for im in ray.images():
        print(im)
        plt.figure(figsize=(8, 6), tight_layout=True)
        ax = plt.gca()
        ax.set_xlabel('X')
        ax.set_ylabel('Y')

        # psf_* for PSF circle
        # image_* for histogram
        im.plot(psf_color='b')

        ax.set_aspect('equal', adjustable='datalim')
        if show:
            plt.show()

    # Plotting d80
    plt.figure(figsize=(8, 6), tight_layout=True)
    ax = plt.gca()
    ax.set_xlabel('off-axis')
    ax.set_ylabel('d80')

    ray.plot('d80_deg', marker='o', linestyle=':')
    ray_rx.plot('d80_deg', marker='s', linestyle='--')

    if show:
        plt.show()

    # Plotting effArea
    plt.figure(figsize=(8, 6), tight_layout=True)
    ax = plt.gca()
    ax.set_xlabel('off-axis')
    ax.set_ylabel('eff. area')

    ray.plot('eff_area', marker='o', linestyle=':')
    ray_rx.plot('d80_deg', marker='s', linestyle='--')

    if show:
        plt.show()


if __name__ == '__main__':

    test_ssts(True)
    test_rx(True)