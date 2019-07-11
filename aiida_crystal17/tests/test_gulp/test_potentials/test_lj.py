from textwrap import dedent
import pytest
from aiida_crystal17.gulp.potentials.lj import PotentialWriterLJ


def test_basic():
    data = {
        "species": ["H core", "He core"],
        "2body": {
            "0.1": {
                "A": 1.0,
                "B": 2.0,
                "rmax": 12.0
            }
        }
    }
    output = PotentialWriterLJ().create_string(data)
    expected = dedent("""\
        lennard 12 6
        H core  He core 1.0 2.0 12.0""")
    assert output == expected


def test_validation():
    with pytest.raises(Exception):
        PotentialWriterLJ().create_string({})
    with pytest.raises(Exception):
        PotentialWriterLJ().create_string({"atoms": {"abc": {}}})


def test_additional_args():
    data = {
        "species": ["Fe core", "B core"],
        "2body": {
            "0.1": {
                "m": 10,
                "n": 5,
                "A": 1.0,
                "B": 2.0,
                "rmin": 3.0,
                "rmax": 12.0
            }
        }
    }
    output = PotentialWriterLJ().create_string(data)
    expected = dedent("""\
        lennard 10 5
        Fe core B core  1.0 2.0 3.0 12.0""")
    assert output == expected


def test_multi():
    data = {
        "species": ["H core", "He core", "B core"],
        "2body": {
            "0.1": {
                "A": 1.0,
                "B": 2.0,
                "rmax": 12.0
            },
            "0.2": {
                "A": 3.0,
                "B": 4.0,
                "rmax": 12.0
            }
        }
    }
    output = PotentialWriterLJ().create_string(data)
    expected = dedent("""\
        lennard 12 6
        H core  He core 1.0 2.0 12.0
        lennard 12 6
        H core  B core  3.0 4.0 12.0""")
    assert output == expected


def test_filter():
    data = {
        "species": ["H core", "He core", "B core"],
        "2body": {
            "0.1": {
                "A": 1.0,
                "B": 2.0,
                "rmax": 12.0
            },
            "0.2": {
                "A": 3.0,
                "B": 4.0,
                "rmax": 12.0
            }
        }
    }
    output = PotentialWriterLJ().create_string(data, ["H core", "B core"])
    expected = dedent("""\
        lennard 12 6
        H core  B core  3.0 4.0 12.0""")
    assert output == expected
