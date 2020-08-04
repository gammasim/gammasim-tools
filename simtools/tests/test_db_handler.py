#!/usr/bin/python3

import logging
import subprocess
from pathlib import Path

import simtools.db_handler as db
import simtools.config as cfg
from simtools.model.telescope_model import TelescopeModel

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

testDataDirectory = './data/test-output'
DB_CTA_SIMULATION_MODEL = 'CTA-Simulation-Model'


def test_reading_db_lst():

    logger.info('----Testing reading LST-----')
    pars = db.getModelParameters('north-lst-1', 'prod4', testDataDirectory)
    assert(pars['parabolic_dish']['Value'] == 1)
    assert(pars['camera_pixels']['Value'] == 1855)

    logger.info('Listing files written in {}'.format(testDataDirectory))
    subprocess.call(['ls -lh {}'.format(testDataDirectory)], shell=True)

    return


def test_reading_db_mst_nc():

    logger.info('----Testing reading MST-NectarCam-----')
    pars = db.getModelParameters('north-mst-nectarcam-d', 'prod4', testDataDirectory)
    assert(pars['camera_pixels']['Value'] == 1855)

    logger.info('Listing files written in {}'.format(testDataDirectory))
    subprocess.call(['ls -lh {}'.format(testDataDirectory)], shell=True)

    logger.info('Removing the files written in {}'.format(testDataDirectory))
    subprocess.call(['rm -f {}/*'.format(testDataDirectory)], shell=True)

    return


def test_reading_db_mst_fc():

    logger.info('----Testing reading MST-FlashCam-----')
    pars = db.getModelParameters('north-mst-flashcam-d', 'prod4', testDataDirectory)
    assert(pars['camera_pixels']['Value'] == 1764)

    logger.info('Listing files written in {}'.format(testDataDirectory))
    subprocess.call(['ls -lh {}'.format(testDataDirectory)], shell=True)

    logger.info('Removing the files written in {}'.format(testDataDirectory))
    subprocess.call(['rm -f {}/*'.format(testDataDirectory)], shell=True)

    return


def test_reading_db_sst():

    logger.info('----Testing reading SST-----')
    pars = db.getModelParameters('south-sst-d', 'prod4', testDataDirectory)
    assert(pars['camera_pixels']['Value'] == 2048)

    logger.info('Listing files written in {}'.format(testDataDirectory))
    subprocess.call(['ls -lh {}'.format(testDataDirectory)], shell=True)

    logger.info('Removing the files written in {}'.format(testDataDirectory))
    subprocess.call(['rm -f {}/*'.format(testDataDirectory)], shell=True)

    return


def test_modify_db():

    logger.info('----Testing copying a whole telescope-----')
    dbClient, tunnel = db.openMongoDB()
    db.copyTelescope(
        dbClient,
        DB_CTA_SIMULATION_MODEL,
        'North-LST-1',
        'prod4',
        'North-LST-Test',
        'sandbox'
    )
    pars = db.readMongoDB(dbClient, 'sandbox', 'North-LST-Test', 'prod4', testDataDirectory)
    assert(pars['camera_pixels']['Value'] == 1855)

    logger.info('----Testing adding a parameter-----')
    db.addParameter(
        dbClient,
        'sandbox',
        'North-LST-Test',
        'camera_config_version',
        'test',
        42
    )
    pars = db.readMongoDB(dbClient, 'sandbox', 'North-LST-Test', 'test', testDataDirectory)
    assert(pars['camera_config_version']['Value'] == 42)

    logger.info('----Testing updating a parameter-----')
    db.updateParameter(
        dbClient,
        'sandbox',
        'North-LST-Test',
        'test',
        'camera_config_version',
        999
    )
    pars = db.readMongoDB(dbClient, 'sandbox', 'North-LST-Test', 'test', testDataDirectory)
    assert(pars['camera_config_version']['Value'] == 999)

    logger.info('----Testing deleting a query (a whole telescope in this case)-----')
    query = {'Telescope': 'North-LST-Test'}
    db.deleteQuery(dbClient, 'sandbox', query)
    db.closeSSHTunnel([tunnel])

    return


# def test_get_model_file():

#     tel = TelescopeModel(
#         telescopeType='lst',
#         site='south',
#         version='prod4',
#         label='test-lst'
#     )

#     fileName = tel.getParameter('camera_config_file')

#     logger.info('FileName = {}'.format(fileName))

#     file = db.getModelFile(fileName)

#     logger.info('FilePath = {}'.format(file))

#     destDir = Path.cwd()
#     db.writeModelFile(fileName, destDir)

#     return


if __name__ == '__main__':

    # test_get_model_file()
    test_reading_db_lst()
    test_reading_db_mst_nc()
    test_reading_db_mst_fc()
    test_reading_db_sst()
    test_modify_db()
    pass
