import os

from aiida_crystal17.tests import TEST_DIR
from aiida_crystal17.parsers.migrate import create_inputs


def test_create_inputs(new_database):
    inpath = os.path.join(TEST_DIR, "input_files", 'nio_sto3g_afm.crystal.d12')
    outpath = os.path.join(TEST_DIR, "output_files",
                           'nio_sto3g_afm.crystal.out')

    inputs = create_inputs(inpath, outpath)

    assert set(inputs.keys()) == set(
        ["parameters", "settings", "structure", "basis"])

    assert set(inputs["basis"].keys()) == set(["Ni", "O"])

    expected_params = {
        'scf': {
            'single': 'UHF',
            'numerical': {
                'FMIXING': 30
            },
            'post_scf': ['PPAN'],
            'spinlock': {
                'SPINLOCK': [0, 15]
            },
            'k_points': [8, 8]
        },
        'title': 'NiO Bulk with AFM spin'
    }

    assert inputs["parameters"].get_dict() == expected_params

    expected_settings = {
        'crystal': {
            'system': 'triclinic',
            'transform': None
        },
        'kinds': {
            'ghosts': [],
            'spin_alpha': ['Ni'],
            'spin_beta': ['Ni1'],
            'fixed': []
        },
        'symmetry': {
            'operations':
            [[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0], [
                0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0
            ], [0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0], [
                -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0
            ], [1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
             [0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0], [
                 -1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0
             ], [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],
             [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0], [
                 0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0
             ], [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
             [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0], [
                 -1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0
             ], [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0], [
                 1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0
             ], [0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0,
                 0.0]],
            'angletol':
            None,
            'sgnum':
            1,
            'symprec':
            0.01
        },
        '3d': {
            'primitive': True,
            'standardize': True,
            'idealize': False
        }
    }

    assert inputs["settings"].get_dict() == expected_settings
