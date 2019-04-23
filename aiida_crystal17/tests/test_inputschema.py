"""
test input schema
"""
import pytest
from aiida_crystal17.validation import validate_against_schema
from jsonschema import ValidationError


def test_toplevel_fail():
    with pytest.raises(ValidationError):
        validate_against_schema({}, "inputd12.schema.json")
    with pytest.raises(ValidationError):
        validate_against_schema({"a": 1}, "inputd12.schema.json")


def test_toplevel_pass():
    data = {
        # "title": "a title",
        # "geometry": {},
        # "basis_set": {},
        "scf": {
            "k_points": [8, 8]
        }
    }
    validate_against_schema(data, "inputd12.schema.json")


def test_full_pass():
    data = {
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
                "xc": ["LDA", "PZ"],
                # or
                # "xc": "HSE06",
                # or
                # "xc": {"LSRSH-PBE": [0.11, 0.25, 0.00001]},
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
                "EXCHPERM": False,
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
            # "fock_mixing": {"BROYDEN": [0.0001, 50, 2]},
            "spinlock": {
                "SPINLOCK": [1, 10]
            },
            "post_scf": ["GRADCAL", "PPAN"]
        }
    }
    validate_against_schema(data, "inputd12.schema.json")
