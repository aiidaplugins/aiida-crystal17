import os
from textwrap import dedent

from click.testing import CliRunner
from aiida_crystal17.cmndline.structsettings import structsettings
from aiida_crystal17.cmndline.basis_set import basisset
from aiida_crystal17.tests import TEST_DIR


def test_settings_show(new_database):

    from aiida.plugins import DataFactory
    setting_cls = DataFactory('crystal17.structsettings')

    symmdata = {
        "operations": [[1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]],
        "space_group": 1,
        "centring_code": 2,
        "crystal_type": 3
    }
    settings_node = setting_cls(data=symmdata)
    settings_node.store()

    runner = CliRunner()
    result = runner.invoke(structsettings, ['show', str(settings_node.pk)])

    assert result.exit_code == 0

    expected = dedent("""\
                centring_code: 2
                crystal_type:  3
                num_symops:    1
                space_group:   1
                """)

    print(result.output)

    assert expected == str(result.output)

    result2 = runner.invoke(structsettings,
                            ['show', "-s", str(settings_node.pk)])

    assert result2.exit_code == 0


def test_basis_show(new_database):

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


def test_basis_upload(new_database):

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
