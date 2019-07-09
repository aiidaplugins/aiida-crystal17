from aiida_crystal17.parsers.raw.inputd12_write import write_input


def test_input_full():
    indict = {
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
            "CHARGED": False,
        },
        "scf": {
            "dft": {
                # "xc": ["LDA", "PZ"],
                # or
                # "xc": "HSE06",
                # or
                "xc": {
                    "LSRSH-PBE": [0.11, 0.25, 0.00001]
                },
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
                "NOBIPCOU": False,
                "NOBIPEXCH": False,
                "NOBIPOLA": False,
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

    outstr = write_input(indict, ["basis_set1", "basis_set2"])

    expected = """a title
EXTERNAL
ATOMSYMM
SYMMOPS
STRUCPRT
OPTGEOM
FULLOPTG
HESSIDEN
NUMGRATO
PRINTFORCES
PRINTOPT
FINALRUN
4
MAXCYCLE
50
TOLDEE
7
TOLDEG
0.0003
TOLDEX
0.0012
ENDOPT
END
basis_set1
basis_set2
99 0
END
DFT
LSRSH-PBE
0.11 0.25 1e-05
SPIN
XLGRID
BECKE
LIMBEK
400
TOLLDENS
6
TOLLGRID
14
END
SHRINK
8 8
BIPOLAR
18 14
BIPOSIZE
4000000
EXCHPERM
EXCHSIZE
4000000
FMIXING
0
ILASIZE
6000
INTGPACK
0
LEVSHIFT
2 1
MADELIND
50
MAXCYCLE
50
POLEORDR
4
SMEAR
0.1
TOLDEE
6
TOLINTEG
6 6 6 6 12
TOLPSEUD
6
DIIS
SPINLOCK
1 10
GRADCAL
PPAN
END
"""

    assert outstr == expected


def test_input_with_atom_props():
    indict = {
        "scf": {
            "k_points": [16, 8]
        },
        "geometry": {
            "optimise": {
                "type": "FULLOPTG"
            }
        }
    }

    atomprops = {
        "spin_alpha": [1, 3],
        "spin_beta": [2, 4],
        "unfixed": [1, 3],
        "ghosts": [5, 6]
    }

    outstr = write_input(indict, ["basis_set1", "basis_set2"], atomprops)

    expected = """CRYSTAL run
EXTERNAL
OPTGEOM
FULLOPTG
FRAGMENT
2
1 3
ENDOPT
END
basis_set1
basis_set2
99 0
GHOSTS
2
5 6
END
SHRINK
16 8
ATOMSPIN
4
1 1
2 -1
3 1
4 -1
END
"""
    assert outstr == expected


def test_is_as_list():
    """ test if the IS value is given as a list"""
    indict = {
        "scf": {
            "k_points": [[10, 8, 2], 16]
        }
    }

    outstr = write_input(indict, ["basis_set1", "basis_set2"])

    expected = """CRYSTAL run
EXTERNAL
END
basis_set1
basis_set2
99 0
END
SHRINK
0 16
10 8 2
END
"""
    assert outstr == expected
