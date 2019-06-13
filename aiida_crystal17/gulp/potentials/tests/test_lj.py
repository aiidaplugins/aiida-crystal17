from textwrap import dedent
import pytest
from aiida_crystal17.gulp.potentials.lj import PotentialWriterLJ


def test_basic():
    data = {
        "atoms": {
            "H": {
                "He": {
                    "A": 1.0,
                    "B": 2.0,
                    "rmax": 12.0
                }
            }
        }
    }
    output = PotentialWriterLJ().create_string(data)
    expected = dedent("""\
        lennard 12 6
        H He 1.0 2.0 12.0""")
    assert output == expected


def test_validation():
    with pytest.raises(Exception):
        PotentialWriterLJ().create_string({})
    with pytest.raises(Exception):
        PotentialWriterLJ().create_string({"atoms": {"abc": {}}})


def test_additional_args():
    data = {
        "m": 10,
        "n": 5,
        "atoms": {
            "Fe": {
                "B": {
                    "A": 1.0,
                    "B": 2.0,
                    "rmin": 3.0,
                    "rmax": 12.0
                }
            }
        }
    }
    output = PotentialWriterLJ().create_string(data)
    expected = dedent("""\
        lennard 10 5
        Fe B 1.0 2.0 3.0 12.0""")
    assert output == expected


def test_multi():
    data = {
        "atoms": {
            "H": {
                "He": {
                    "A": 1.0,
                    "B": 2.0,
                    "rmax": 12.0
                },
                "B": {
                    "A": 3.0,
                    "B": 4.0,
                    "rmax": 12.0
                }
            }
        }
    }
    output = PotentialWriterLJ().create_string(data)
    expected = dedent("""\
        lennard 12 6
        H B 3.0 4.0 12.0
        H He 1.0 2.0 12.0""")
    assert output == expected


def test_filter():
    data = {
        "atoms": {
            "H": {
                "He": {
                    "A": 1.0,
                    "B": 2.0,
                    "rmax": 12.0
                },
                "B": {
                    "A": 3.0,
                    "B": 4.0,
                    "rmax": 12.0
                }
            }
        }
    }
    output = PotentialWriterLJ().create_string(data, ["H", "B"])
    expected = dedent("""\
        lennard 12 6
        H B 3.0 4.0 12.0""")
    assert output == expected
