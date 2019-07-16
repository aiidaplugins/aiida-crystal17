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
        H core  He core 1.00000000E+00 2.00000000E+00 12.00000""")
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
        Fe core B core  1.00000000E+00 2.00000000E+00  3.00000 12.00000""")
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
        H core  He core 1.00000000E+00 2.00000000E+00 12.00000
        lennard 12 6
        H core  B core  3.00000000E+00 4.00000000E+00 12.00000""")
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
        H core  B core  3.00000000E+00 4.00000000E+00 12.00000""")
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
    output = PotentialWriterLJ().create_content(
        data, fitting_data=fitting_data)
    expected = dedent("""\
        lennard 12 6
        H core  He core 1.00000000E+00 2.00000000E+00 12.00000 0 1
        lennard 12 6
        H core  B core  3.00000000E+00 4.00000000E+00 12.00000 1 0""")
    assert output.content == expected


def test_read_existing():
    content = dedent("""\
        variables
        shift
        end
        lennard 12 6
        H core  He shell 1.00000000E+00 2.00000000E+00 12.00000 0 1
        H core  H core 3.00000000E+00 4.00000000E+00 12.00000 0 1
        lennard 10 5
        H B 5.00000000E+00 6.00000000E+00 0.00 12.00000 1 0
        dump fitting.grs
        """)

    data = PotentialWriterLJ().read_exising(content.splitlines())
    assert data == {
        'species': ['B core', 'H core', 'He shell'],
        '2body': {
            '1-2': {
                'lj_m': 12,
                'lj_n': 6,
                'lj_A': 1.0,
                'lj_B': 2.0,
                'lj_rmax': 12.0
            },
            '1-1': {
                'lj_m': 12,
                'lj_n': 6,
                'lj_A': 3.0,
                'lj_B': 4.0,
                'lj_rmax': 12.0
            },
            '1-0': {
                'lj_m': 10,
                'lj_n': 5,
                'lj_A': 5.0,
                'lj_B': 6.0,
                'lj_rmin': 0.0,
                'lj_rmax': 12.0
            }
        }
    }
