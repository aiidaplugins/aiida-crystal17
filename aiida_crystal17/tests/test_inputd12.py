from aiida_crystal17.parsers.inputd12 import write_input


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
END
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
GRADCAL
PPAN
END
"""

    assert outstr == expected
