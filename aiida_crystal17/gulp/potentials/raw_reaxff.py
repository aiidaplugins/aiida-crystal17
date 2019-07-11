from decimal import Decimal
import re

from aiida_crystal17.validation import validate_against_schema
from aiida_crystal17.gulp.potentials.common import INDEX_SEP


KEYS_GLOBAL = (
    'Overcoordination 1', 'Overcoordination 2', 'Valency angle conjugation 1',
    'Triple bond stabilisation 1', 'Triple bond stabilisation 2',
    'C2-correction', 'Undercoordination 1', 'Triple bond stabilisation',
    'Undercoordination 2', 'Undercoordination 3',
    'Triple bond stabilization energy', 'Lower Taper-radius',
    'Upper Taper-radius', 'reaxff2_bo10', 'Valency undercoordination',
    'Valency angle/lone pair', 'Valency angle 1', 'Valency angle 2',
    'Not used 2', 'Double bond/angle', 'Double bond/angle: overcoord 1',
    'Double bond/angle: overcoord 2', 'Not used 3', 'Torsion/BO',
    'Torsion overcoordination 1', 'Torsion overcoordination 2', 'Not used 4',
    'Conjugation', 'vdWaals shielding', 'bond order cutoff',
    'Valency angle conjugation 2', 'Valency overcoordination 1',
    'Valency overcoordination 2', 'Valency/lone pair', 'Not used 5',
    'Not used 6', 'Not used 7', 'Not used 8', 'Valency angle conjugation 3'
)

KEYS_1BODY = (
    'reaxff1_radii1', 'reaxff1_valence1', 'mass',
    'reaxff1_morse3', 'reaxff1_morse2', 'reaxff_gamma', 'reaxff1_radii2',
    'reaxff1_valence3', 'reaxff1_morse1', 'reaxff1_morse4', 'reaxff1_valence4',
    'reaxff1_under', 'dummy1', 'reaxff_chi', 'reaxff_mu', 'dummy2',
    'reaxff1_radii3', 'reaxff1_lonepair2', 'dummy3', 'reaxff1_over2',
    'reaxff1_over1', 'reaxff1_over3', 'dummy4', 'dummy5', 'reaxff1_over4',
    'reaxff1_angle1', 'dummy11', 'reaxff1_valence2', 'reaxff1_angle2',
    'dummy6', 'dummy7', 'dummy8'
)

KEYS_2BODY_BONDS = (
    'reaxff2_bond1', 'reaxff2_bond2', 'reaxff2_bond3',
    'reaxff2_bond4', 'reaxff2_bo5', 'reaxff2_bo7', 'reaxff2_bo6',
    'reaxff2_over', 'reaxff2_bond5', 'reaxff2_bo3', 'reaxff2_bo4', 'dummy1',
    'reaxff2_bo1', 'reaxff2_bo2', 'reaxff2_bo8', 'reaxff2_bo9'
)

KEYS_2BODY_OFFDIAG = [
    'reaxff2_morse1', 'reaxff2_morse3', 'reaxff2_morse2',
    'reaxff2_morse4', 'reaxff2_morse5', 'reaxff2_morse6'
]

KEYS_3BODY_ANGLES = (
    'reaxff3_angle1', 'reaxff3_angle2',
    'reaxff3_angle3', 'reaxff3_conj', 'reaxff3_angle5', 'reaxff3_penalty',
    'reaxff3_angle4'
)

KEYS_3BODY_HBOND = (
    'reaxff3_hbond1', 'reaxff3_hbond2',
    'reaxff3_hbond3', 'reaxff3_hbond4'
)

KEYS_4BODY_TORSION = (
    'reaxff4_torsion1', 'reaxff4_torsion2',
    'reaxff4_torsion3', 'reaxff4_torsion4', 'reaxff4_torsion5', 'dummy1',
    'dummy2'
)

DEFAULT_TOLERANCES = {
    "anglemin": 0.001,
    "angleprod": 0.001,  # Hard coded to 0.001 in original code.
    "hbondmin": 0.01,  # Hard coded to 0.01 in original code.
    "hbonddist": 7.5,  # Hard coded to 7.5 Ang in original code.
    "torsionprod": 0.00001
}
# NB: torsionprod needs to be lower (0.001), to get comparable energy to lammps,
# but then won't optimize (reaches maximum steps)


def split_numbers(string, as_decimal=False):
    """ get a list of numbers from a string (even with no spacing)

    :type string: str
    :type as_decimal: bool
    :param as_decimal: if True return floats as decimal.Decimal objects

    :rtype: list

    :Example:

    >>> split_numbers("1")
    [1.0]

    >>> split_numbers("1 2")
    [1.0, 2.0]

    >>> split_numbers("1.1 2.3")
    [1.1, 2.3]

    >>> split_numbers("1e-3")
    [0.001]

    >>> split_numbers("-1-2")
    [-1.0, -2.0]

    >>> split_numbers("1e-3-2")
    [0.001, -2.0]

    """
    _match_number = re.compile(
        '-?\\ *[0-9]+\\.?[0-9]*(?:[Ee]\\ *[+-]?\\ *[0-9]+)?')
    string = string.replace(" .", " 0.")
    string = string.replace("-.", "-0.")
    return [
        Decimal(s) if as_decimal else float(s)
        for s in re.findall(_match_number, string)
    ]


def read_lammps_format(lines):
    """ read a reaxff file, in lammps format, to a standardised potential dictionary """
    output = {
        "description": lines[0],
        "global": {},
        "species": ["X core"],  # X is always first
        "1body": {},
        "2body": {},
        "3body": {},
        "4body": {}
    }

    lineno = 1

    # Global parameters
    if lines[lineno].split()[0] != str(len(KEYS_GLOBAL)):
        raise IOError('Expecting {} global parameters'.format(len(KEYS_GLOBAL)))

    for key in KEYS_GLOBAL:
        lineno += 1
        output["global"][key] = float(lines[lineno].split()[0])

    # one-body parameters
    lineno += 1
    num_species = int(lines[lineno].split()[0])
    lineno += 3
    idx = 1
    for i in range(num_species):
        lineno += 1
        symbol, values = lines[lineno].split(None, 1)
        if symbol == "X":
            species_idx = 0  # the X symbol is always assigned index 0
        else:
            species_idx = idx
            idx += 1
            output["species"].append(symbol + " core")
        values = split_numbers(values)
        for _ in range(3):
            lineno += 1
            values.extend(split_numbers(lines[lineno]))

        if len(values) != len(KEYS_1BODY):
            raise Exception(
                'number of values different than expected for species {0}, '
                '{1} != {2}'.format(symbol, len(values), len(KEYS_1BODY)))

        key_map = {k: v for k, v in zip(KEYS_1BODY, values)}
        key_map['reaxff1_lonepair1'] = 0.5 * (key_map["reaxff1_valence3"] - key_map["reaxff1_valence1"])

        output["1body"][str(species_idx)] = key_map

    # two-body bond parameters
    lineno += 1
    num_lines = int(lines[lineno].split()[0])
    lineno += 2
    for _ in range(num_lines):
        values = split_numbers(lines[lineno]) + split_numbers(lines[lineno + 1])
        species_idx1 = int(values.pop(0))
        species_idx2 = int(values.pop(0))
        key_name = "{}-{}".format(species_idx1, species_idx2)
        lineno += 2

        if len(values) != len(KEYS_2BODY_BONDS):
            raise Exception(
                'number of bond values different than expected for key {0}, '
                '{1} != {2}'.format(key_name, len(values), len(KEYS_2BODY_BONDS)))

        output["2body"][key_name] = {k: v for k, v in zip(KEYS_2BODY_BONDS, values)}

    # two-body off-diagonal parameters
    num_lines = int(lines[lineno].split()[0])
    lineno += 1
    for _ in range(num_lines):
        values = split_numbers(lines[lineno])
        species_idx1 = int(values.pop(0))
        species_idx2 = int(values.pop(0))
        key_name = "{}-{}".format(species_idx1, species_idx2)
        lineno += 1

        if len(values) != len(KEYS_2BODY_OFFDIAG):
            raise Exception(
                'number of off-diagonal values different than expected for key {0} (line {1}), '
                '{2} != {3}'.format(key_name, lineno-1, len(values), len(KEYS_2BODY_OFFDIAG)))

        output["2body"].setdefault(key_name, {}).update({k: v for k, v in zip(KEYS_2BODY_OFFDIAG, values)})

    # three-body angle parameters
    num_lines = int(lines[lineno].split()[0])
    lineno += 1
    for _ in range(num_lines):
        values = split_numbers(lines[lineno])
        species_idx1 = int(values.pop(0))
        species_idx2 = int(values.pop(0))
        species_idx3 = int(values.pop(0))
        key_name = "{}-{}-{}".format(species_idx1, species_idx2, species_idx3)
        lineno += 1

        if len(values) != len(KEYS_3BODY_ANGLES):
            raise Exception(
                'number of angle values different than expected for key {0} (line {1}), '
                '{2} != {3}'.format(key_name, lineno-1, len(values), len(KEYS_3BODY_ANGLES)))

        output["3body"].setdefault(key_name, {}).update({k: v for k, v in zip(KEYS_3BODY_ANGLES, values)})

    # four-body torsion parameters
    num_lines = int(lines[lineno].split()[0])
    lineno += 1
    for _ in range(num_lines):
        values = split_numbers(lines[lineno])
        species_idx1 = int(values.pop(0))
        species_idx2 = int(values.pop(0))
        species_idx3 = int(values.pop(0))
        species_idx4 = int(values.pop(0))
        key_name = "{}-{}-{}-{}".format(species_idx1, species_idx2, species_idx3, species_idx4)
        lineno += 1

        if len(values) != len(KEYS_4BODY_TORSION):
            raise Exception(
                'number of torsion values different than expected for key {0} (line {1}), '
                '{2} != {3}'.format(key_name, lineno-1, len(values), len(KEYS_4BODY_TORSION)))

        output["4body"].setdefault(key_name, {}).update({k: v for k, v in zip(KEYS_4BODY_TORSION, values)})

    # three-body h-bond parameters
    num_lines = int(lines[lineno].split()[0])
    lineno += 1
    for _ in range(num_lines):
        values = split_numbers(lines[lineno])
        species_idx1 = int(values.pop(0))
        species_idx2 = int(values.pop(0))
        species_idx3 = int(values.pop(0))
        key_name = "{}-{}-{}".format(species_idx1, species_idx2, species_idx3)
        lineno += 1

        if len(values) != len(KEYS_3BODY_HBOND):
            raise Exception(
                'number of h-bond values different than expected for key {0} (line {1}), '
                '{2} != {3}'.format(key_name, lineno-1, len(values), len(KEYS_3BODY_HBOND)))

        output["3body"].setdefault(key_name, {}).update({k: v for k, v in zip(KEYS_3BODY_HBOND, values)})

    return output


def format_lammps_value(value):
    return "{:.4f}".format(value)


def write_lammps_format(data):
    """ write a reaxff file, in lammps format, from a standardised potential dictionary """
    # validate dictionary
    validate_against_schema(data, "potential.reaxff.schema.json")

    output = [
        data["description"]
    ]

    # Global parameters
    output.append("{} ! Number of general parameters".format(len(KEYS_GLOBAL)))
    for key in KEYS_GLOBAL:
        output.append("{0:.4f} ! {1}".format(data["global"][key], key))

    # one-body parameters
    output.extend([
        '{0} ! Nr of atoms; cov.r; valency;a.m;Rvdw;Evdw;gammaEEM;cov.r2;#'.format(len(data["species"])),
        'alfa;gammavdW;valency;Eunder;Eover;chiEEM;etaEEM;n.u.',
        'cov r3;Elp;Heat inc.;n.u.;n.u.;n.u.;n.u.',
        'ov/un;val1;n.u.;val3,vval4'
    ])
    for i, species in enumerate(data["species"]):
        if species.endswith("shell"):
            raise ValueError("only core species can be used for reaxff, not shell: {}".format(species))
        species = species[:-5]
        output.extend([
            species + " " + " ".join([format_lammps_value(data["1body"][str(i)][k]) for k in KEYS_1BODY[:8]]),
            " ".join([format_lammps_value(data["1body"][str(i)][k]) for k in KEYS_1BODY[8:16]]),
            " ".join([format_lammps_value(data["1body"][str(i)][k]) for k in KEYS_1BODY[16:24]]),
            " ".join([format_lammps_value(data["1body"][str(i)][k]) for k in KEYS_1BODY[24:32]])
        ])

    # two-body angle parameters
    suboutout = []
    for key in sorted(data["2body"]):
        subdata = data["2body"][key]
        if not set(subdata.keys()).issuperset(KEYS_2BODY_BONDS):
            continue
        suboutout.extend([
            " ".join(key.split(INDEX_SEP)) + " " + " ".join(
                [format_lammps_value(subdata[k]) for k in KEYS_2BODY_BONDS[:8]]),
            " ".join([format_lammps_value(subdata[k]) for k in KEYS_2BODY_BONDS[8:16]])
        ])

    output.extend([
        '{0} ! Nr of bonds; Edis1;LPpen;n.u.;pbe1;pbo5;13corr;pbo6'.format(int(len(suboutout)/2)),
        'pbe2;pbo3;pbo4;n.u.;pbo1;pbo2;ovcorr'
    ] + suboutout)

    # two-body off-diagonal parameters
    suboutout = []
    for key in sorted(data["2body"]):
        subdata = data["2body"][key]
        if not set(subdata.keys()).issuperset(KEYS_2BODY_OFFDIAG):
            continue
        suboutout.extend([
            " ".join(key.split(INDEX_SEP)) + " " + " ".join(
                [format_lammps_value(subdata[k]) for k in KEYS_2BODY_OFFDIAG]),
        ])

    output.extend([
        '{0} ! Nr of off-diagonal terms; Ediss;Ro;gamma;rsigma;rpi;rpi2'.format(len(suboutout))
    ] + suboutout)

    # three-body angle parameters
    suboutout = []
    for key in sorted(data["3body"]):
        subdata = data["3body"][key]
        if not set(subdata.keys()).issuperset(KEYS_3BODY_ANGLES):
            continue
        suboutout.extend([
            " ".join(key.split(INDEX_SEP)) + " " + " ".join(
                [format_lammps_value(subdata[k]) for k in KEYS_3BODY_ANGLES]),
        ])

    output.extend([
        '{0} ! Nr of angles;at1;at2;at3;Thetao,o;ka;kb;pv1;pv2'.format(len(suboutout))
    ] + suboutout)

    # four-body torsion parameters
    suboutout = []
    for key in sorted(data["4body"]):
        subdata = data["4body"][key]
        if not set(subdata.keys()).issuperset(KEYS_4BODY_TORSION):
            continue
        suboutout.extend([
            " ".join(key.split(INDEX_SEP)) + " " + " ".join(
                [format_lammps_value(subdata[k]) for k in KEYS_4BODY_TORSION]),
        ])

    output.extend([
        '{0} ! Nr of torsions;at1;at2;at3;at4;;V1;V2;V3;V2(BO);vconj;n.u;n'.format(len(suboutout))
    ] + suboutout)

    # three-body h-bond parameters
    suboutout = []
    for key in sorted(data["3body"]):
        subdata = data["3body"][key]
        if not set(subdata.keys()).issuperset(KEYS_3BODY_HBOND):
            continue
        suboutout.extend([
            " ".join(key.split(INDEX_SEP)) + " " + " ".join(
                [format_lammps_value(subdata[k]) for k in KEYS_3BODY_HBOND]),
        ])

    output.extend([
        '{0} ! Nr of hydrogen bonds;at1;at2;at3;Rhb;Dehb;vhb1'.format(len(suboutout))
    ] + suboutout)

    output.append("")

    return "\n".join(output)


def write_gulp_format(data):
    """ write a reaxff file, in GULP format, from a standardised potential dictionary """
    # validate dictionary
    validate_against_schema(data, "potential.reaxff.schema.json")

    for species in data["species"]:
        if species.endswith("shell"):
            raise ValueError("only core species can be used for reaxff, not shell: {}".format(species))
        species = species[:-5]

    # header
    output = [
        '#',
        '#  ReaxFF force field',
        '#',
        '#  Original paper:',
        '#',
        '#  A.C.T. van Duin, S. Dasgupta, F. Lorant and W.A. Goddard III,',
        '#  J. Phys. Chem. A, 105, 9396-9409 (2001)',
        '#',
        '#  Parameters description:',
        '#',
        '# {}'.format(data["description"]),
        '#',
        '#  Cutoffs for VDW & Coulomb terms',
        '#',
        'reaxFFvdwcutoff {:12.4f}'.format(data["global"]['Upper Taper-radius']),
        'reaxFFqcutoff   {:12.4f}'.format(data["global"]['Upper Taper-radius']),
        '#',
        '#  Bond order threshold - check anglemin as this is cutof2 given in control file',
        '#',
        'reaxFFtol  {:10.8f} {:10.8f} {:10.8f} {:10.8f} {:7.5f} {:10.8f}'.format(
            data["global"]['bond order cutoff'] * 0.01,
            *[data["global"].get(k, DEFAULT_TOLERANCES[k])
              for k in "anglemin angleprod hbondmin hbonddist torsionprod".split()]
        ),
        '#',
    ]
    # NOTE: there is a line length issue,
    # whereby if the decimal places in reaxFFtol are too large, then the result is altered

    # global parameters
    output.append("#  Species independent parameters")
    output.append("#")
    output.append(("reaxff0_bond     {:12.6f} {:12.6f}".format(
        data["global"]['Overcoordination 1'],
        data["global"]['Overcoordination 2'])))
    output.append(("reaxff0_over     {:12.6f} {:12.6f} {:12.6f} {:12.6f} {:12.6f}".format(
        data["global"]['Valency overcoordination 2'],
        data["global"]['Valency overcoordination 1'],
        data["global"]['Undercoordination 1'],
        data["global"]['Undercoordination 2'],
        data["global"]['Undercoordination 3'])))
    output.append(("reaxff0_valence  {:12.6f} {:12.6f} {:12.6f} {:12.6f}".format(
        data["global"]['Valency undercoordination'],
        data["global"]['Valency/lone pair'],
        data["global"]['Valency angle 1'],
        data["global"]['Valency angle 2'])))
    output.append(("reaxff0_penalty  {:12.6f} {:12.6f} {:12.6f}".format(
        data["global"]['Double bond/angle'],
        data["global"]['Double bond/angle: overcoord 1'],
        data["global"]['Double bond/angle: overcoord 2'])))
    output.append(("reaxff0_torsion  {:12.6f} {:12.6f} {:12.6f} {:12.6f}".format(
        data["global"]['Torsion/BO'],
        data["global"]['Torsion overcoordination 1'],
        data["global"]['Torsion overcoordination 2'],
        data["global"]['Conjugation'])))
    output.append("reaxff0_vdw      {:12.6f}".format(
        data["global"]['vdWaals shielding']))
    output.append("reaxff0_lonepair {:12.6f}".format(
        data["global"]['Valency angle/lone pair']))

    # one-body parameters
    output.append("#")
    output.append("#  One-Body Parameters")
    output.append("#")

    fields = {
        'reaxff1_radii': ['reaxff1_radii1', 'reaxff1_radii2', 'reaxff1_radii3'],
        'reaxff1_valence': ['reaxff1_valence1', 'reaxff1_valence2', 'reaxff1_valence3', 'reaxff1_valence4'],
        'reaxff1_over': ['reaxff1_over1', 'reaxff1_over2', 'reaxff1_over3', 'reaxff1_over4'],
        'reaxff1_under kcal': ['reaxff1_under'],
        'reaxff1_lonepair kcal': ['reaxff1_lonepair1', 'reaxff1_lonepair2'],
        'reaxff1_angle': ['reaxff1_angle1', 'reaxff1_angle2'],
        'reaxff1_morse kcal': ['reaxff1_morse1', 'reaxff1_morse2', 'reaxff1_morse3', 'reaxff1_morse4'],
        'reaxff_chi': ['reaxff_chi'],
        'reaxff_mu': ['reaxff_mu'],
        'reaxff_gamma': ['reaxff_gamma']
    }

    output.extend(create_gulp_fields(data, "1body", fields))

    # two-body bond parameters
    output.append("#")
    output.append("#  Two-Body Parameters")
    output.append("#")

    fields = {
        'reaxff2_bo over bo13': [
            'reaxff2_bo1', 'reaxff2_bo2', 'reaxff2_bo3',
            'reaxff2_bo4', 'reaxff2_bo5', 'reaxff2_bo6'],
        'reaxff2_bo bo13': [
            'reaxff2_bo1', 'reaxff2_bo2', 'reaxff2_bo3',
            'reaxff2_bo4', 'reaxff2_bo5', 'reaxff2_bo6'],
        'reaxff2_bo over': [
            'reaxff2_bo1', 'reaxff2_bo2', 'reaxff2_bo3',
            'reaxff2_bo4', 'reaxff2_bo5', 'reaxff2_bo6'],
        'reaxff2_bo': [
            'reaxff2_bo1', 'reaxff2_bo2', 'reaxff2_bo3',
            'reaxff2_bo4', 'reaxff2_bo5', 'reaxff2_bo6'],
        'reaxff2_bond kcal': [
            'reaxff2_bond1', 'reaxff2_bond2', 'reaxff2_bond3',
            'reaxff2_bond4', 'reaxff2_bond5'],
        'reaxff2_over': ['reaxff2_over'],
        'reaxff2_pen kcal': ['reaxff2_bo9'],
        'reaxff2_morse kcal': [
            'reaxff2_morse1', 'reaxff2_morse2', 'reaxff2_morse3',
            'reaxff2_morse4', 'reaxff2_morse5', 'reaxff2_morse6']
    }

    conditions = {
        'reaxff2_bo over bo13': lambda s: s['reaxff2_bo7'] > 0.001 and s['reaxff2_bo8'] > 0.001,
        'reaxff2_bo bo13': lambda s: s['reaxff2_bo7'] > 0.001 and s['reaxff2_bo8'] <= 0.001,
        'reaxff2_bo over': lambda s: s['reaxff2_bo7'] <= 0.001 and s['reaxff2_bo8'] > 0.001,
        'reaxff2_bo': lambda s: s['reaxff2_bo7'] <= 0.001 and s['reaxff2_bo8'] <= 0.001,
        'reaxff2_pen kcal': lambda s: s['reaxff2_bo9'] > 0.0
    }

    append_values = {
        'reaxff2_pen kcal': [data['global']['reaxff2_bo10'], 1.0]
    }

    output.extend(create_gulp_fields(data, "2body", fields, append_values, conditions))

    # three-body parameters
    output.append("#")
    output.append("#  Three-Body Parameters")
    output.append("#")

    fields = {
        'reaxff3_angle kcal': [
            'reaxff3_angle1', 'reaxff3_angle2', 'reaxff3_angle3',
            'reaxff3_angle4', 'reaxff3_angle5'],
        'reaxff3_penalty kcal': ['reaxff3_penalty'],
        'reaxff3_conjugation kcal': ['reaxff3_conj'],
        'reaxff3_hbond kcal': [
            'reaxff3_hbond1', 'reaxff3_hbond2',
            'reaxff3_hbond3', 'reaxff3_hbond4']
    }

    conditions = {
        'reaxff3_angle kcal': lambda s: s['reaxff3_angle2'] > 0.0,
        'reaxff3_conjugation kcal': lambda s: abs(s['reaxff3_conj']) > 1.0E-4
    }

    append_values = {
        'reaxff3_conjugation kcal': [
            data["global"]['Valency angle conjugation 1'],
            data["global"]['Valency angle conjugation 3'],
            data["global"]['Valency angle conjugation 2']
        ]
    }

    output.extend(create_gulp_fields(data, "3body", fields, append_values, conditions))

    # one-body parameters
    output.append("#")
    output.append("#  Four-Body Parameters")
    output.append("#")

    fields = {
        'reaxff4_torsion kcal': [
            'reaxff4_torsion1', 'reaxff4_torsion2', 'reaxff4_torsion3',
            'reaxff4_torsion4', 'reaxff4_torsion5'],
    }

    output.extend(create_gulp_fields(data, "4body", fields))

    output.append("")

    return "\n".join(output)


def create_gulp_fields(data, data_key, fields, append_values=None, conditions=None):
    """ create a subsection of the gulp output file"""
    if conditions is None:
        conditions = {}
    if append_values is None:
        append_values = {}

    output = []

    for field in sorted(fields):
        keys = fields[field]
        subdata = []
        for indices in sorted(data[data_key]):
            if not set(data[data_key][indices].keys()).issuperset(keys):
                continue
            if field in conditions:
                try:
                    satisfied = conditions[field](data[data_key][indices])
                except KeyError:
                    continue
                if not satisfied:
                    continue
            species = ["{:7s}".format(data["species"][int(i)]) for i in indices.split(INDEX_SEP)]
            if len(species) == 3:
                # NOTE Here species1 is the pivot atom of the three-body like term.
                # This is different to LAMMPS, where the pivot atom is the central one!
                species = [species[1], species[0], species[2]]
            species = " ".join(species)
            values = " ".join([format_gulp_value(data[data_key][indices], k) for k in keys])
            if field in append_values:
                values += " " + " ".join(["{:8.4f} ".format(v) for v in append_values[field]])
            subdata.append("{} {}".format(species, values))
        if subdata:
            output.append(field)
            output.extend(subdata)

    return output


def format_gulp_value(data, key):
    """ some GULP specific conversions """
    value = data[key]

    if key == "reaxff2_bo3":
        # If reaxff2_bo3 = 1 needs to be set to 0 for GULP since this is a dummy value
        value = 0.0 if abs(value - 1) < 1e-12 else value

    elif key == 'reaxff2_bo5':
        # If reaxff2_bo(5,n) < 0 needs to be set to 0 for GULP since this is a dummy value
        value = 0.0 if value < 0.0 else value

    elif key == 'reaxff1_radii3':
        # TODO, this wasn't part of the original script, and should be better understood
        # but without it, the energies greatly differ to LAMMPS (approx equal otherwise)
        value = 0.0 if value > 0.0 else value

    return "{:8.4f} ".format(value)
