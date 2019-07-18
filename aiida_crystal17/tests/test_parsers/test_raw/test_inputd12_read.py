import os

from aiida_crystal17.tests import TEST_FILES
import pytest
from aiida_crystal17.parsers.raw.inputd12_read import extract_data
from jsonextended import edict


@pytest.fixture("function")
def input_str():
    return """a title
EXTERNAL
ATOMSYMM
SYMMOPS
STRUCPRT
OPTGEOM
FULLOPTG
HESSIDEN
NUMGRATO
PRINTOPT
PRINTFORCES
MAXCYCLE
50
TOLDEX
0.0012
FINALRUN
4
TOLDEG
0.0003
TOLDEE
7
FRAGMENT
2
1 3
ENDOPT
END
12 3
1 0 3  2.  0.
1 1 3  8.  0.
1 1 3  2.  0.
8 8
0 0 6 2.0 1.0
 27032.382631 0.00021726302465
 4052.3871392 0.00168386621990
 922.32722710 0.00873956162650
 261.24070989 0.03523996880800
 85.354641351 0.11153519115000
 31.035035245 0.25588953961000
0 0 2 2.0 1.0
 12.260860728 0.39768730901000
 4.9987076005 0.24627849430000
0 0 1 0.0 1.0
 1.0987136000 1.00000000000000
0 0 1 0.0 1.0
 0.3565870100 1.00000000000000
0 2 4 4.0 1.0
 63.274954801 0.0060685103418
 14.627049379 0.0419125758240
 4.4501223456 0.1615384108800
 1.5275799647 0.3570695131100
0 2 1 0.0 1.0
 0.5489735000 1.0000000000000
0 2 1 0.0 1.0
 0.1858671100 1.0000000000000
0 3 1 0.0 1.0
 0.2534621300 1.0000000000000
99 0
CHARGED
GHOSTS
2
5 6
END
DFT
EXCHANGE
LDA
CORRELAT
PZ
SPIN
XLGRID
BECKE
TOLLDENS
6
LIMBEK
400
TOLLGRID
14
END
SHRINK
8 8
INTGPACK
0
FMIXING
0
EXCHPERM
SMEAR
0.1
TOLPSEUD
6
POLEORDR
4
EXCHSIZE
4000000
ILASIZE
6000
MAXCYCLE
50
BIPOLAR
18 14
MADELIND
50
TOLINTEG
6 6 6 6 12
BIPOSIZE
4000000
LEVSHIFT
2 1
TOLDEE
6
DIIS
SPINLOCK
1 10
ATOMSPIN
4
1 1
2 -1
3 1
4 -1
GRADCAL
PPAN
END
"""


def test_read_fail(input_str):
    input_str = input_str.replace("PPAN", "WRONG")
    with pytest.raises(NotImplementedError):
        extract_data(input_str)


def test_full_read(input_str):
    output_dict, basis_sets, atom_props = extract_data(input_str)

    assert len(basis_sets) == 2

    assert atom_props == {
        'fragment': [1, 3],
        'ghosts': [5, 6],
        'spin_alpha': [1, 3],
        'spin_beta': [2, 4]
    }

    expected = {
        "title": "a title",
        "geometry": {
            "info_print": ["ATOMSYMM", "SYMMOPS"],
            "info_external": ["STRUCPRT"],
            "optimise": {
                "type": "FULLOPTG",
                "hessian": "HESSIDEN",
                "gradient": "NUMGRATO",
                "info_print": ["PRINTOPT", "PRINTFORCES"],
                "convergence": {
                    "TOLDEG": 0.0003,
                    "TOLDEX": 0.0012,
                    "TOLDEE": 7,
                    "MAXCYCLE": 50,
                    "FINALRUN": 4
                },
            }
        },
        "basis_set": {
            "CHARGED": True,
        },
        "scf": {
            "dft": {
                "xc": ["LDA", "PZ"],
                # or
                # "xc": "HSE06",
                # or
                # "xc": {
                #     "LSRSH-PBE": [0.11, 0.25, 0.00001]
                # },
                "SPIN": True,
                "grid": "XLGRID",
                "grid_weights": "BECKE",
                "numerical": {
                    "TOLLDENS": 6,
                    "TOLLGRID": 14,
                    "LIMBEK": 400
                }
            },
            # or
            # "single": "UHF",
            "k_points": [8, 8],
            "numerical": {
                "BIPOLAR": [18, 14],
                "BIPOSIZE": 4000000,
                "EXCHSIZE": 4000000,
                "EXCHPERM": True,
                "ILASIZE": 6000,
                "INTGPACK": 0,
                "MADELIND": 50,
                "POLEORDR": 4,
                "TOLINTEG": [6, 6, 6, 6, 12],
                "TOLPSEUD": 6,
                "FMIXING": 0,
                "MAXCYCLE": 50,
                "TOLDEE": 6,
                "LEVSHIFT": [2, 1],
                "SMEAR": 0.1
            },
            "fock_mixing": "DIIS",
            # or
            # "fock_mixing": ["BROYDEN", 0.0001, 50, 2],
            "spinlock": {
                "SPINLOCK": [1, 10]
            },
            "post_scf": ["GRADCAL", "PPAN"]
        }
    }

    assert edict.diff(output_dict, expected) == {}


def test_mgo_sto3g_scf():
    path = os.path.join(TEST_FILES, "crystal", "mgo_sto3g_scf", 'INPUT')
    with open(path) as f:
        input_str = f.read()

    output_dict, basis_sets, atom_props = extract_data(input_str)

    assert len(basis_sets) == 2

    assert atom_props == {}

    assert output_dict == {'scf': {'k_points': (8, 8)}, 'title': 'MgO bulk'}


def test_mgo_sto3g_opt():
    path = os.path.join(TEST_FILES, "crystal", "mgo_sto3g_opt", 'INPUT')
    with open(path) as f:
        input_str = f.read()

    output_dict, basis_sets, atom_props = extract_data(input_str)

    assert len(basis_sets) == 2

    assert atom_props == {}

    assert output_dict == {
        'geometry': {
            'optimise': {
                'type': 'FULLOPTG'
            }
        },
        'scf': {
            'k_points': (8, 8)
        },
        'title': 'MgO bulk'
    }


def test_nio_sto3g_afm():
    path = os.path.join(TEST_FILES, "crystal", "nio_sto3g_afm_scf", 'INPUT')
    with open(path) as f:
        input_str = f.read()

    output_dict, basis_sets, atom_props = extract_data(input_str)

    assert len(basis_sets) == 2

    assert atom_props == {'spin_alpha': [1], 'spin_beta': [2]}

    assert output_dict == {
        'scf': {
            'single': 'UHF',
            'numerical': {
                'FMIXING': 30
            },
            'post_scf': ['PPAN'],
            'spinlock': {
                'SPINLOCK': [0, 15]
            },
            'k_points': (8, 8)
        },
        'title': 'NiO Bulk with AFM spin'
    }
