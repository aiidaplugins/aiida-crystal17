from textwrap import dedent
import pytest
from aiida_crystal17.gulp.potentials.lj import PotentialWriterLJ


def test_basic():
    data = {
        "species": ["H core", "He core"],
        "2body": {
            "0-1": {
                "lj_A": 1.0,
                "lj_B": 2.0,
                "lj_rmax": 12.0
            }
        }
    }
    output = PotentialWriterLJ().create_content(data)
    expected = dedent("""\
        lennard 12 6
        H core  He core 1.0 2.0 12.0""")
    assert output.content == expected


def test_validation():
    with pytest.raises(Exception):
        PotentialWriterLJ().create_content({})
    with pytest.raises(Exception):
        PotentialWriterLJ().create_content({"atoms": {"abc": {}}})


def test_additional_args():
    data = {
        "species": ["Fe core", "B core"],
        "2body": {
            "0-1": {
                "lj_m": 10,
                "lj_n": 5,
                "lj_A": 1.0,
                "lj_B": 2.0,
                "lj_rmin": 3.0,
                "lj_rmax": 12.0
            }
        }
    }
    output = PotentialWriterLJ().create_content(data)
    expected = dedent("""\
        lennard 10 5
        Fe core B core  1.0 2.0 3.0 12.0""")
    assert output.content == expected


def test_multi():
    data = {
        "species": ["H core", "He core", "B core"],
        "2body": {
            "0-1": {
                "lj_A": 1.0,
                "lj_B": 2.0,
                "lj_rmax": 12.0
            },
            "0-2": {
                "lj_A": 3.0,
                "lj_B": 4.0,
                "lj_rmax": 12.0
            }
        }
    }
    output = PotentialWriterLJ().create_content(data)
    expected = dedent("""\
        lennard 12 6
        H core  He core 1.0 2.0 12.0
        lennard 12 6
        H core  B core  3.0 4.0 12.0""")
    assert output.content == expected


def test_filter():
    data = {
        "species": ["H core", "He core", "B core"],
        "2body": {
            "0-1": {
                "lj_A": 1.0,
                "lj_B": 2.0,
                "lj_rmax": 12.0
            },
            "0-2": {
                "lj_A": 3.0,
                "lj_B": 4.0,
                "lj_rmax": 12.0
            }
        }
    }
    output = PotentialWriterLJ().create_content(data, ["H core", "B core"])
    expected = dedent("""\
        lennard 12 6
        H core  B core  3.0 4.0 12.0""")
    assert output.content == expected


def test_add_fitting_flags():
    data = {
        "species": ["H core", "He core", "B core"],
        "2body": {
            "0-1": {
                "lj_A": 1.0,
                "lj_B": 2.0,
                "lj_rmax": 12.0
            },
            "0-2": {
                "lj_A": 3.0,
                "lj_B": 4.0,
                "lj_rmax": 12.0
            }
        }
    }
    fitting_data = {
        "species": ["H core", "He core", "B core"],
        "2body": {
            "0-1": ["lj_B"],
            "0-2": ["lj_A"]
        }
    }
    output = PotentialWriterLJ().create_content(data, fitting_data=fitting_data)
    expected = dedent("""\
        lennard 12 6
        H core  He core 1.0 2.0 12.0 0 1
        lennard 12 6
        H core  B core  3.0 4.0 12.0 1 0""")
    assert output.content == expected
