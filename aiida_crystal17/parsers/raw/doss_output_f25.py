import traceback

import ejplugins
from ejplugins.crystal import CrystalDOSPlugin

from aiida_crystal17 import __version__


def read_doss_f25_content(fileobj, parser_class):

    results_data = {
        "parser_version": str(__version__),
        "parser_class": str(parser_class),
        "ejplugins_version": str(ejplugins.__version__),
        "parser_errors": [],
        "parser_warnings": [],
        "errors": [],
        "warnings": []
    }

    parser = CrystalDOSPlugin()
    try:
        read_data = parser.read_file(fileobj, log_warnings=False)
    except IOError as err:
        traceback.print_exc()
        results_data["parser_errors"].append(
            "Error parsing CRYSTAL 17 main output: {0}".format(err))
        return results_data, None

    results_data["fermi_energy"] = read_data["fermi_energy"]["magnitude"]
    results_data["energy_units"] = read_data["fermi_energy"]["units"]
    results_data["system_type"] = read_data["system_type"]

    array_data = {}

    array_data["energies"] = read_data["energy"]["magnitude"]
    results_data["npts"] = len(array_data["energies"])
    results_data["energy_max"] = max(array_data["energies"])
    results_data["energy_min"] = min(array_data["energies"])

    total_alpha = read_data["total_alpha"]["dos"]
    results_data["norbitals_total"] = read_data["total_alpha"]["norbitals"]
    if read_data["total_beta"] is not None:
        results_data["spin"] = True
        total_beta = read_data["total_beta"]["dos"]
        assert len(total_alpha) == len(total_beta)
    else:
        results_data["spin"] = False

    if read_data["projections_alpha"] is not None:
        results_data["norbitals_projections"] = [p["norbitals"] for p in read_data["projections_alpha"]]
        projected_alpha = [p["dos"] for p in read_data["projections_alpha"]]
    if read_data["projections_beta"] is not None:
        projected_beta = [p["dos"] for p in read_data["projections_beta"]]
        assert len(projected_alpha) == len(projected_beta)

    if read_data["total_beta"] is None:
        array_data["total"] = total_alpha
    else:
        array_data["total_alpha"] = total_alpha
        array_data["total_beta"] = total_beta

    if read_data["projections_alpha"] is not None:
        if read_data["projections_beta"] is not None:
            array_data["projections_alpha"] = total_alpha
            array_data["projections_beta"] = total_beta
        else:
            array_data["projections"] = total_alpha

    return results_data, array_data
