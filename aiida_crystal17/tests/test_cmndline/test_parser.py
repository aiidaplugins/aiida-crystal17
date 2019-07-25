import os
from click.testing import CliRunner
from aiida_crystal17.cmndline.cmd_parser import parse
from aiida_crystal17.tests import TEST_FILES


def test_parse_stdin_fail():
    runner = CliRunner()
    result = runner.invoke(parse, ['stdin', ''])
    assert result.exit_code != 0, result.stdout


def test_parse_stdin():
    runner = CliRunner()
    result = runner.invoke(parse, ['stdin', os.path.join(TEST_FILES, 'crystal', 'mgo_sto3g_scf', 'INPUT')])
    assert result.exit_code == 0, result.stdout


def test_parse_stdout_fail():
    runner = CliRunner()
    result = runner.invoke(parse, ['stdout', ''])
    assert result.exit_code != 0, result.stdout


def test_parse_stdout():
    runner = CliRunner()
    result = runner.invoke(parse, ['stdout', os.path.join(TEST_FILES, 'crystal', 'mgo_sto3g_scf', 'main.out')])
    assert result.exit_code == 0, result.stdout
