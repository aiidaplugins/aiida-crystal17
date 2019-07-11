from aiida_crystal17.gulp.parsers.raw.write_geometry import create_geometry_lines


def create_input_lines(potential, structures, observables):
    """ create the input file for a potential fitting """
    lines = []

    # intial key words
    lines.append("fit noflags")
    lines.append("")

    # The following command makes a uniform shift
    # to the energies of all structures to remove
    # the constant offset => we are only fitting
    # the local curvature.
    lines.extend(["shift", str(1.0)])
    lines.append("")

    for name in sorted(structures.keys()):
        lines.extend(create_geometry_lines(structures[name], name=name))
        lines.append("")
        observe = observables[name]
        lines.append("observables")
        # TODO units conversion
        # TODO set which observables keys to set via settings dict
        # TODO set weightings per structure
        lines.append("energy ev")
        lines.append("{0:.8f} {1:.8f}".format(observe["energy"], 100.0))
        lines.append("end")
        lines.append("")

    # Tell the program to fit the overall shift
    lines.extend(["vary", "shift", "end"])
    lines.append("")

    # Force Field
    lines.extend(potential.get_input_lines())

    # TODO optional dumping
    # dump every {interval} noover fitting.grs

    lines.append("")

    return lines
