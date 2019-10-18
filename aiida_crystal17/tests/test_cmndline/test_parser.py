from click.testing import CliRunner

from aiida_crystal17.cmndline.cmd_parser import stdin, stdout, doss_f25
from aiida_crystal17.tests import resource_context


def test_parse_stdin_fail():
    """Test parsing no file path."""
    runner = CliRunner()
    result = runner.invoke(stdin, [''])
    assert result.exit_code != 0, result.stdout


def test_parse_stdin():
    """Test parsing good stdin file."""
    runner = CliRunner()
    with resource_context('crystal', 'mgo_sto3g_scf', 'INPUT') as path:
        result = runner.invoke(stdin, [str(path)])
    assert result.exit_code == 0, result.stdout


def test_parse_stdout_fail():
    """Test parsing no file path."""
    runner = CliRunner()
    result = runner.invoke(stdout, [''])
    assert result.exit_code != 0, result.stdout


def test_parse_stdout():
    """Test parsing good stdout file."""
    runner = CliRunner()
    with resource_context('crystal', 'mgo_sto3g_scf', 'main.out') as path:
        result = runner.invoke(stdout, [str(path)])
    assert result.exit_code == 0, result.stdout


def test_parse_doss_f25():
    """Test parsing good fort.25 file."""
    runner = CliRunner()
    with resource_context('doss', 'mgo_sto3g_scf', 'fort.25') as path:
        result = runner.invoke(doss_f25, [str(path)])
    assert result.exit_code == 0, result.stdout
