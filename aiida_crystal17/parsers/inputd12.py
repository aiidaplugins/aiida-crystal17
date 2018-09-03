"""
module to read and write CRYSTAL17 .d12 files
"""
from aiida_crystal17.parsers import validate_dict

# TODO float format and rounding, e.g. "{}".format(0.00001) -> 1e-05, can CRYSTAL handle that?

# TODO SHRINK where IS=0 and IS1 IS2 IS3 given
# TODO FIELD/FIELDCON
# TODO FREQCALC
# TODO ANHARM
# TODO EOS

# TODO RESTART (need to provide files from previous remote folder)
# TODO fixing atoms (FRAGMENT), could do by kind but I'm not sure how this would play with using kind to reduce symmetry
# TODO initial spin based on kind


def get_keys(dct, keys, default=None, raise_error=False):
    """retrieve the leaf of a key path from a dictionary"""
    subdct = dct
    for i, key in enumerate(keys):
        if key in subdct:
            subdct = subdct[key]
        elif raise_error:
            raise ValueError("could not find key path: {}".format(
                keys[0:i + 1]))
        else:
            return default
    return subdct


def format_value(dct, keys):
    """return the value + a new line, or empty string if keys not found"""
    value = get_keys(dct, keys, None)
    if value is None:
        return ""
    if isinstance(value, dict):
        outstr = ""
        for keyword in value.keys():
            args = value[keyword]
            if isinstance(args, bool):
                if args:
                    outstr += "{}\n".format(keyword)
            elif isinstance(args, (list, tuple)):
                outstr += "{0}\n{1}\n".format(keyword,
                                              " ".join([str(a) for a in args]))
            else:
                outstr += "{0}\n{1}\n".format(keyword, args)
        return outstr

    return "{}\n".format(value)


def write_input(indict, basis_sets):
    """write input of a validated input dictionay"""

    validate_dict(indict)

    outstr = ""

    # Title
    title = get_keys(indict, ["title"], "")
    outstr += "{}\n".format(" ".join(title.splitlines()))  # must be one line

    # Geometry
    outstr += "EXTERNAL\n"  # we assume external geometry

    # Geometry Optional Keywords (including optimisation)
    for keyword in get_keys(indict, ["geometry", "info_print"], []):
        outstr += "{}\n".format(keyword)
    for keyword in get_keys(indict, ["geometry", "info_external"], []):
        outstr += "{}\n".format(keyword)

    if "optimise" in indict["geometry"]:
        outstr += "OPTGEOM\n"
        outstr += format_value(indict, ["geometry", "optimise", "type"])
        outstr += format_value(indict, ["geometry", "optimise", "hessian"])
        outstr += format_value(indict, ["geometry", "optimise", "gradient"])
        for keyword in get_keys(indict, ["geometry", "optimise", "info_print"],
                                []):
            outstr += "{}\n".format(keyword)
        outstr += format_value(indict, ["geometry", "optimise", "convergence"])
        outstr += "END\n"

    # Geometry End
    outstr += "END\n"

    # Basis Sets
    for basis_set in basis_sets:
        outstr += "{}\n".format(basis_set.strip())
    outstr += "99 0\n"

    # Basis Sets Optional Keywords
    outstr += format_value(indict, ["basis_set"])

    # Basis Sets End
    outstr += "END\n"

    # Hamiltonian Optional Keywords
    outstr += format_value(indict, ["scf", "single"])
    # DFT Optional Block
    if get_keys(indict, ["scf", "dft"], False):

        outstr += "DFT\n"

        xc = get_keys(indict, ["scf", "dft", "xc"], raise_error=True)
        if isinstance(xc, (tuple, list)):
            if len(xc) == 2:
                outstr += "CORRELAT\n"
                outstr += "{}\n".format(xc[0])
                outstr += "EXCHANGE\n"
                outstr += "{}\n".format(xc[1])
        else:
            outstr += format_value(indict, ["scf", "dft", "xc"])

        if get_keys(indict, ["scf", "dft", "SPIN"], False):
            outstr += "SPIN\n"

        outstr += format_value(indict, ["scf", "dft", "grid"])
        outstr += format_value(indict, ["scf", "dft", "grid_weights"])
        outstr += format_value(indict, ["scf", "dft", "numerical"])

        outstr += "END\n"

    # # K-POINTS (SHRINK\nPMN Gilat)
    outstr += "SHRINK\n"
    outstr += "{0} {1}\n".format(
        *get_keys(indict, ["scf", "k_points"], raise_error=True))

    # SCF/Other Optional Keywords
    outstr += format_value(indict, ["scf", "numerical"])
    outstr += format_value(indict, ["scf", "fock_mixing"])
    outstr += format_value(indict, ["scf", "spinlock"])
    for keyword in get_keys(indict, ["scf", "post_scf"], []):
        outstr += "{}\n".format(keyword)

    # Hamiltonian and SCF End
    outstr += "END\n"

    return outstr
