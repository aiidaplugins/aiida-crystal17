import os
from click.testing import CliRunner
from aiida_crystal17.cmndline.cmd_parser import stdin, stdout, doss_f25
from aiida_crystal17.tests import TEST_FILES


def test_parse_stdin_fail():
    runner = CliRunner()
    result = runner.invoke(stdin, [''])
    assert result.exit_code != 0, result.stdout


def test_parse_stdin():
    runner = CliRunner()
    result = runner.invoke(stdin, [os.path.join(TEST_FILES, 'crystal', 'mgo_sto3g_scf', 'INPUT')])
    assert result.exit_code == 0, result.stdout


def test_parse_stdout_fail():
    runner = CliRunner()
    result = runner.invoke(stdout, [''])
    assert result.exit_code != 0, result.stdout


def test_parse_stdout():
    runner = CliRunner()
    result = runner.invoke(stdout, [os.path.join(TEST_FILES, 'crystal', 'mgo_sto3g_scf', 'main.out')])
    assert result.exit_code == 0, result.stdout


def test_parse_doss_f25():
    runner = CliRunner()
    result = runner.invoke(doss_f25, [os.path.join(TEST_FILES, 'doss', 'mgo_sto3g_scf', 'fort.25')])
    assert result.exit_code == 0, result.stdout
