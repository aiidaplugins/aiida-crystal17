import os
from textwrap import dedent

from click.testing import CliRunner
from aiida_crystal17.cmndline.symmetry import symmetry
from aiida_crystal17.cmndline.basis_set import basisset
from aiida_crystal17.tests import TEST_DIR


def test_symmetry_show(db_test_app):

    from aiida.plugins import DataFactory
    node_cls = DataFactory('crystal17.symmetry')

    symmdata = {
        "operations": [[1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]],
        "hall_number": 1,
        "basis": "fractional"
    }
    node = node_cls(data=symmdata)
    node.store()

    runner = CliRunner()
    result = runner.invoke(symmetry, ['show', str(node.pk)])

    assert result.exit_code == 0

    expected = dedent("""\
                basis:       fractional
                hall_number: 1
                num_symops:  1
                """)

    print(result.output)

    assert expected == str(result.output)

    result2 = runner.invoke(symmetry,
                            ['show', "-s", str(node.pk)])

    assert result2.exit_code == 0


def test_basis_show(db_test_app):

    from aiida.plugins import DataFactory
    basis_cls = DataFactory('crystal17.basisset')
    node, created = basis_cls.get_or_create(
        os.path.join(TEST_DIR, "input_files", "sto3g", 'sto3g_O.basis'))

    runner = CliRunner()
    result = runner.invoke(basisset, ['show', str(node.pk)])

    assert result.exit_code == 0

    expected = """\
        atomic_number: 8
        author:        John Smith
        basis_type:    all-electron
        class:         sto3g
        element:       O
        filename:      sto3g_O.basis
        md5:           73a9c7315dc6edf6ab8bd4427a66f31c
        num_shells:    2
        year:          1999
        """

    assert dedent(expected) == str(result.output)

    result2 = runner.invoke(basisset, ['show', '-c', str(node.pk)])

    assert result2.exit_code == 0


def test_basis_upload(db_test_app):

    path = os.path.join(TEST_DIR, "input_files", "sto3g")
    runner = CliRunner()
    result = runner.invoke(basisset, [
        'uploadfamily', '--path', path, '--name', 'sto3g', '--description',
        'STO3G'
    ])

    print(result.output)

    assert result.exit_code == 0

    result2 = runner.invoke(basisset, ['listfamilies', '-d'])

    print(result2.output)

    assert result2.exit_code == 0

    assert 'sto3g' in result2.output
