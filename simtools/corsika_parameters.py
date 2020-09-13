''' Parameters for corsika_config module. '''

import astropy.units as u

__all__ = [
    'USER_PARAMETERS',
    'PRIMARIES',
    'SITE_PARAMETERS',
    'INTERACTION_FLAGS',
    'CHERENKOV_EMISSION_PARS',
    'DEBUGGING_OUTPUT_PARAMETERS',
    'IACT_TUNING_PARAMETERS'
]

USER_PARAMETERS = {
    'RUNNR': {'len': 1, 'names': ['RUNNUMBER', 'NRUN'], 'default': 1},
    'EVTNR': {'len': 1, 'names': ['EVENTNR', 'EVENTNUMBER'], 'default': 1},
    'NSHOW': {'len': 1, 'names': ['NSHOWERS']},
    'PRMPAR': {'len': 1, 'names': ['PRIMARY']},
    'ERANGE': {'len': 2, 'names': ['ENRANGE', 'ENERGYRANGE'], 'unit': [u.TeV] * 2},
    'ESLOPE': {'len': 1, 'names': ['ENSLOPE', 'ENERGYSLOPE']},
    'THETAP': {'len': 2, 'names': ['THETA', 'ZENITH'], 'unit': [u.deg] * 2},
    'PHIP': {'len': 1, 'names': ['PHI', 'AZIMUTH'], 'unit': u.deg},
    'VIEWCONE': {'len': 2, 'names': ['CONE'], 'unit': [u.deg] * 2},
    'CSCAT': {'len': 3, 'names': [], 'unit': [None, u.cm, None]}
}


PRIMARIES = {
    'GAMMA': {'number': 1, 'names': ['PHOTON']},
    'ELECTRON': {'number': 3, 'names': ['ELECTRONS']},
    'PROTON': {'number': 14, 'names': ['PROTONS']},
    'HELIUM': {'number': 402, 'names': []}
}

SITE_PARAMETERS = {
    'South': {
        'OBSLEV': [2150.e2],
        'ATMOSPHERE': [26, 'Y'],
        'MAGNET': [20.925, -9.119],
        'ARRANG':  [-3.433]
    },
    'North': {
        'OBSLEV': [2158.e2],
        'ATMOSPHERE': [36, 'Y'],
        'MAGNET': [30.576, 23.571],
        'ARRANG': [-5.3195]
    }
}

INTERACTION_FLAGS = {
    'FIXHEI': [0., 0],
    'FIXCHI': [0.],
    'TSTART': ['T'],
    'ECUTS': [0.3, 0.1, 0.020, 0.020],
    'MUADDI': ['F'],
    'MUMULT': ['T'],
    'LONGI': ['T', 20., 'F', 'F'],
    'MAXPRT': [0],
    'ECTMAP': [1.e6],
    'STEPFC': [1.0]
}

CHERENKOV_EMISSION_PARAMETERS = {
    'CERSIZ': [5.],
    'CERFIL': ['F'],
    'CWAVLG': [240., 700.]
}

DEBUGGING_OUTPUT_PARAMETERS = {
    'DEBUG': ['F', 6, 'F', 1000000],
    'DATBAS': ['yes'],
    'DIRECT': [r'/dev/null']
}

IACT_TUNING_PARAMETERS = {
    'IACT': [
        ['SPLIT_AUTO', '15M'],
        ['IO_BUFFER', '800MB'],
        ['MAX_BUNCHES', '1000000']
    ]
}

# Telescopes info
TELESCOPE_Z = {  # Z coordinate in m
    'LST': 16.,
    'MST': 10.,
    'SST': 5.
}

TELESCOPE_SPHERE_RADIUS = {  # Radius of the sphere in m
    'LST': 12.5,
    'MST': 7.,
    'SST': 3.5
}
