"""
parse the main.gout file of a GULP run and create the required output nodes
"""
from collections import Mapping
import traceback

from aiida.plugins import DataFactory
from aiida.engine import ExitCode

from aiida_crystal17 import __version__
from aiida_crystal17.gulp.calculations.gulp_abstract import GulpAbstractCalculation


class OutputNodes(Mapping):
    """
    a mapping of output nodes, with attribute access
    """
    def __init__(self):
        self._dict = {
            "results": None,
            "structure": None
        }

    def _get_results(self):
        return self._dict["results"]

    def _set_results(self, value):
        assert isinstance(value, DataFactory('dict'))
        self._dict["results"] = value

    results = property(_get_results, _set_results)

    def _get_structure(self):
        return self._dict["structure"]

    def _set_structure(self, value):
        assert isinstance(value, DataFactory('structure'))
        self._dict["structure"] = value

    structure = property(_get_structure, _set_structure)

    def __getitem__(self, value):
        out = self._dict[value]
        if out is None:
            raise KeyError(value)
        return out

    def __iter__(self):
        for key, val in self._dict.items():
            if val is not None:
                yield key

    def __len__(self):
        len([k for k, v in self._dict.items() if v is not None])


class ParserResult(object):
    def __init__(self):
        self.exit_code = ExitCode()  # initialises as (0, None)
        self.nodes = OutputNodes()


# pylint: disable=too-many-locals,too-many-statements
def parse_output(file_handle, parser_class, exit_codes=None, final=False, optimise=False):
    """ parse the main output file and create the required output nodes

    :param file_handle: handle to main output file
    :param parser_class: a string denoting the parser class
    :param exit_codes: allowed exit codes
        (defaults to ``GulpAbstractCalculation.exit_codes``)
    :param final: whether to expect a 'final' key in the results_data
    :param optimise: whether to expect an 'optimised' key in the results_data

    :return parse_result

    """
    parser_result = ParserResult()
    if exit_codes is None:
        exit_codes = GulpAbstractCalculation.exit_codes

    results_data = {
        'parser_version': __version__,
        'parser_class': str(parser_class),
        'parser_errors': [],
        'parser_warnings': [],
        "warnings": [],
        "errors": []
    }

    try:
        _parse_main_output(file_handle.read(), results_data)
    except KeyError as err:
        traceback.print_exc()
        parser_result.exit_code = exit_codes.ERROR_OUTPUT_PARSING
        results_data['parser_errors'].append("{}".format(err))
        return parser_result

    if "optimised" in results_data and not results_data["optimised"]:
        parser_result.exit_code = exit_codes.ERROR_NOT_OPTIMISED
    elif results_data['errors']:
        parser_result.exit_code = exit_codes.ERROR_GULP_RUN
    elif optimise and "optimised" not in results_data:
        parser_result.exit_code = exit_codes.ERROR_NOT_OPTIMISED

    idata = None
    fdata = None
    if "initial" in results_data:
        idata = results_data.pop('initial')
    else:
        results_data['parser_errors'].append("expected 'initial' data")
        parser_result.exit_code = exit_codes.ERROR_OUTPUT_PARSING
    if 'final' in results_data:
        fdata = results_data.pop('final')
    elif final:
        results_data['parser_errors'].append("expected 'final' data")
        parser_result.exit_code = exit_codes.ERROR_OUTPUT_PARSING

    if final:
        if idata:
            results_data['energy_initial'] = idata['lattice_energy']['primitive']
        if fdata:
            results_data['energy'] = fdata['lattice_energy']['primitive']
    elif idata:
        results_data['energy'] = idata['lattice_energy']['primitive']

    parser_result.nodes.results = DataFactory("dict")(dict=results_data)

    return parser_result


def _parse_main_output(outstr, data):

    data["energy_units"] = "eV"

    lines = outstr.splitlines()

    while lines:
        line, fields = _new_line(lines)

        # if ' '.join(fields[:4]) == 'Total number atoms/shells =':
        #     data['natoms'] = int(fields[4])
        # elif ' '.join(fields[:2]) == 'Formula =':
        #     data['formula'] = fields[2]

        if line.startswith('!! ERROR'):
            data["errors"].append(line)
            return data

        if line.startswith('!! WARNING'):
            data["warnings"].append(line)

        if ' '.join(fields[:4]) == '**** Optimisation achieved ****':
            data['optimised'] = True
        elif "Conditions for a minimum have not been satisfied. However" in line:
            data['optimised'] = True
            data['warnings'].append(
                ("Conditions for a minimum have not been satisfied. "
                 "However no lower point can be found - treat results with caution"))
        elif "No variables to optimise - single point performed" in line:
            data['optimised'] = True
            data['warnings'].append(
                "No variables to optimise - single point performed")
        elif ' '.join(
                fields[:4]) == '**** Too many failed' and len(fields) > 5:
            if fields[6] == 'optimise':
                data['optimised'] = False
                data['errors'].append(line)
        elif ' '.join(fields[:2]) == '**** Maximum' and len(fields) > 7:
            if ' '.join(fields[4:5] + [fields[8]]) == 'function calls reached':
                data['optimised'] = False
                data['errors'].append(line)

        elif ' '.join(fields[:4]) == 'Total lattice energy =':
            _extract_lattice_energy_prim_only(data, fields)

        elif ' '.join(fields[:4]) == 'Total lattice energy :':
            _extract_lattice_energy(data, lines)

        elif ' '.join(fields[:4]) == 'ReaxFF : Energy contributions:':
            _extract_energy_contribs(data, lines)

        # TODO Total CPU time, num_opt_steps, charges (reaxff only)


def _extract_lattice_energy_prim_only(data, fields):
    """extract energy when there is only a primitive cell"""
    units = ' '.join(fields[5:])
    if units == 'eV':

        energy = float(fields[4])

        etype = 'initial'
        if 'initial' in data:
            if 'lattice_energy' in data['initial']:
                if 'final' not in data:
                    data['final'] = {}
                etype = 'final'
        else:
            data['initial'] = {}
        data[etype]['lattice_energy'] = {}
        data[etype]['lattice_energy']['primitive'] = energy


def _extract_lattice_energy(data, lines):
    """extract energy when there is a primitive and conventional cell"""
    etype = 'initial'
    if 'initial' in data:
        if 'lattice_energy' in data['initial']:
            if 'final' not in etype:
                data['final'] = {}
            etype = 'final'
    else:
        data['initial'] = {}

    data[etype]['lattice_energy'] = {}

    line, fields = _new_line(lines)
    has_primitive = _assert_true(
        data, fields[0] == 'Primitive', "expecting primitive energy", line)
    has_energy_ev = _assert_true(
        data, fields[5] == 'eV', "expecting energy in eV", line)
    if (has_primitive and has_energy_ev):
        data[etype]['lattice_energy']['primitive'] = float(fields[4])

    line, fields = _new_line(lines)
    has_non_primitive = _assert_true(
        data, fields[0] == 'Non-primitive',
        "expecting non-primitive energy", line)
    has_energy_ev = _assert_true(
        data, fields[5] == 'eV', "expecting energy in eV", line)
    if has_non_primitive and has_energy_ev:
        data[etype]['lattice_energy']['conventional'] = float(fields[4])


def _extract_energy_contribs(data, lines):
    data['energy_contributions'] = {}
    line, fields = _new_line(lines, 2)
    while "=" in line and "E" in line:
        name = _reaxff_ename_map[fields[0][2:-1]]
        if _assert_true(data, fields[3] == 'eV', "expecting energy in eV",
                        line):
            data['energy_contributions'][name] = float(fields[2])
        line, fields = _new_line(lines)


def _new_line(lines, num_lines=1):
    line = ''
    fields = []
    for _ in range(num_lines):
        line = lines.pop(0).strip()
        fields = line.split()
    return line, fields


def _assert_true(data, condition, msg, line):
    if not condition:
        data["errors"].append("Parsing Error: {} for line: {}".format(
            msg, line))
        return False
    return True


_reaxff_ename_map = {
    'bond': 'Bond',
    'bpen': 'Double-Bond Valence Angle Penalty',
    'lonepair': 'Lone-Pair',
    'over': 'Coordination (over)',
    'under': 'Coordination (under)',
    'val': 'Valence Angle',
    'pen': 'Double-Bond Valence Angle Penalty',
    'coa': 'Valence Angle Conjugation',
    'tors': 'Torsion',
    'conj': 'Conjugation',
    'hb': 'Hydrogen Bond',
    'vdw': 'van der Waals',
    'coulomb': 'Coulomb',
    'self': 'Charge Equilibration'
}
