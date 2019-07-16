from textwrap import dedent

from aiida_crystal17.gulp.potentials.base import PotentialWriterAbstract


def test_read_atom_section():

    section = dedent("""\
        H core  He shell 1.00000000E+00 2.00000000E+00 12.00000 0 1
        H B 3.00000000E+00 4.00000000E+00 0.00 12.00000 1 0
        """).splitlines()

    output = PotentialWriterAbstract.read_atom_section(
        section, lineno=0, number_atoms=2, global_args=None)

    assert output == (1, {'B core', 'H core', 'He shell'}, {
        ('H core', 'He shell'): {
            'values': '1.00000000E+00 2.00000000E+00 12.00000 0 1',
            'global': None
        },
        ('H core', 'B core'): {
            'values': '3.00000000E+00 4.00000000E+00 0.00 12.00000 1 0',
            'global': None
        }
    })


def test_read_atom_section_with_break():

    section = dedent("""\
        H core  He shell 1.00000000E+00 2.00000000E+00 12.00000 0 1
        H B 3.00000000E+00 4.00000000E+00 0.00 12.00000 1 0
        lennard 6 12
        """).splitlines()

    output = PotentialWriterAbstract.read_atom_section(
        section, lineno=0, number_atoms=2, global_args=None)

    assert output == (1, {'B core', 'H core', 'He shell'}, {
        ('H core', 'He shell'): {
            'values': '1.00000000E+00 2.00000000E+00 12.00000 0 1',
            'global': None
        },
        ('H core', 'B core'): {
            'values': '3.00000000E+00 4.00000000E+00 0.00 12.00000 1 0',
            'global': None
        }
    })


def test_read_atom_section_with_line_break():

    section = dedent("""\
        H core  He shell 1.00000000E+00 2.00000000E+00 12.00000 0 1
        H B 3.00000000E+00 4.00000000E+00 &
            0.00 12.00000 1 0
        """).splitlines()

    output = PotentialWriterAbstract.read_atom_section(
        section, lineno=0, number_atoms=2, global_args=None)

    assert output == (2, {'B core', 'H core', 'He shell'}, {
        ('H core', 'He shell'): {
            'values': '1.00000000E+00 2.00000000E+00 12.00000 0 1',
            'global': None
        },
        ('H core', 'B core'): {
            'values': '3.00000000E+00 4.00000000E+00 0.00 12.00000 1 0',
            'global': None
        }
    })
