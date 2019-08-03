from click.testing import CliRunner
from aiida_crystal17.cmndline.cmd_parser import stdin, stdout, doss_f25
from aiida_crystal17.tests import get_resource_path


def test_parse_stdin_fail():
    runner = CliRunner()
    result = runner.invoke(stdin, [''])
    assert result.exit_code != 0, result.stdout


def test_parse_stdin():
    runner = CliRunner()
    result = runner.invoke(stdin, [get_resource_path('crystal', 'mgo_sto3g_scf', 'INPUT')])
    assert result.exit_code == 0, result.stdout


def test_parse_stdout_fail():
    runner = CliRunner()
    result = runner.invoke(stdout, [''])
    assert result.exit_code != 0, result.stdout


def test_parse_stdout():
    runner = CliRunner()
    result = runner.invoke(stdout, [get_resource_path('crystal', 'mgo_sto3g_scf', 'main.out')])
    assert result.exit_code == 0, result.stdout


def test_parse_doss_f25():
    runner = CliRunner()
    result = runner.invoke(doss_f25, [get_resource_path('doss', 'mgo_sto3g_scf', 'fort.25')])
    assert result.exit_code == 0, result.stdout
