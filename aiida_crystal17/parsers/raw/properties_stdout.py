#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Chris Sewell
#
# This file is part of aiida-crystal17.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms and conditions
# of version 3 of the GNU Lesser General Public License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
"""Parse the stdout content from a CRYSTAL Properties computation."""
import re

from aiida_crystal17.common.parsing import convert_units, split_numbers
from .crystal_stdout import (
    SYSTEM_INFO_REGEXES,
    ParsedSection,
    assign_exit_code,
    parse_calculation_header,
    parse_pre_header,
    parse_section,
    strip_non_program_output,
)

INPUT_WF_REGEXES = (
    (
        "k_points",
        re.compile(r"\sSHRINK. FACT.\(MONKH.\)\s*(\d+)\s*(\d+)\s*(\d+)", re.DOTALL),
    ),
    ("gilat_net", re.compile(r"\sSHRINKING FACTOR\(GILAT NET\)\s*(\d+)", re.DOTALL)),
    ("energy_total", re.compile(r"TOTAL ENERGY\s*([\+\-\d\.E]+)", re.DOTALL)),
    ("energy_kinetic", re.compile(r"KIN. ENERGY\s*([\+\-\d\.E]+)", re.DOTALL)),
    ("energy_fermi", re.compile(r"FERMI ENERGY\s*([\+\-\d\.E]+)", re.DOTALL)),
)

NEWK_WF_REGEXES = (
    (
        "k_points",
        re.compile(r"\sSHRINK FACTORS\(MONK.\)\s*(\d*)\s*(\d*)\s*(\d*)", re.DOTALL),
    ),
    ("gilat_net", re.compile(r"\sSHRINK FACTOR\(GILAT\)\s*(\d*)", re.DOTALL)),
    ("n_kpoints_ibz", re.compile(r"\sPOINTS IN THE IBZ\s*(\d*)", re.DOTALL)),
    ("n_kpoints_gilat", re.compile(r"\sPOINTS\(GILAT NET\)\s*(\d*)", re.DOTALL)),
)


def read_properties_stdout(content):
    """Parse the stdout content from a CRYSTAL Properties computation to a dict.

    NOTE: this function expects that NEWK is the initial part of the computation
    """
    output = {
        "units": {"conversion": "CODATA2014", "energy": "eV"},
        "errors": [],
        "warnings": [],
        "parser_errors": [],
        "parser_exceptions": [],
    }

    # strip non program output
    content, warnings = strip_non_program_output(content)
    output["warnings"] += warnings
    lines = content.splitlines()

    if not lines:
        output["parser_errors"] += ["the file is empty"]
        return assign_exit_code(output)

    # make an initial parse to find all errors/warnings and start lines for sections
    errors, run_warnings, parser_errors, telapse_seconds, start_lines = initial_parse(
        lines
    )
    output["errors"] += errors
    output["warnings"] += run_warnings
    output["parser_errors"] += errors
    if telapse_seconds is not None:
        output["execution_time_seconds"] = telapse_seconds

    lineno = 0

    # parse until the program header
    outcome = parse_section(parse_pre_header, lines, lineno, output, "non_program")
    if outcome is None or outcome.parser_error is not None:
        return assign_exit_code(output)
    lineno = outcome.next_lineno

    # parse the program header section
    outcome = parse_section(parse_calculation_header, lines, lineno, output, "header")
    if outcome is None or outcome.parser_error is not None:
        return assign_exit_code(output)
    lineno = outcome.next_lineno

    # TODO parse geometry

    outcome = parse_section(parse_calculation_inputs, lines, lineno, output, "wf_input")
    if outcome is None or outcome.parser_error is not None:
        return assign_exit_code(output)
    lineno = outcome.next_lineno

    outcome = parse_section(parse_newk_params, lines, lineno, output, "newk")
    if outcome is None or outcome.parser_error is not None:
        return assign_exit_code(output)
    lineno = outcome.next_lineno

    output = assign_exit_code(output)

    return output


def initial_parse(lines):
    """Scan the file for errors, and find the final elapsed time value."""
    errors = []
    warnings = []
    parser_errors = []
    mpi_abort = False
    telapse_line = None
    start_lines = {}
    found_endprop = False

    for lineno, line in enumerate(lines):

        if "WARNING" in line.upper():
            warnings.append(line.strip())
        elif "ERROR" in line:
            # TODO ignore errors before program execution (e.g. in mpiexec setup)?
            if "open_hca: getaddr_netdev ERROR" not in line:
                errors.append(line.strip())
        elif "MPI_Abort" in line:
            # only record one mpi_abort event (to not clutter output)
            if not mpi_abort:
                errors.append(line.strip())
                mpi_abort = True
        elif "CONVERGENCE TESTS UNSATISFIED" in line.upper():
            errors.append(line.strip())
        elif "TELAPSE" in line:
            telapse_line = lineno
        elif line.strip().startswith("ENDPROP"):
            found_endprop = True

    total_seconds = None
    if telapse_line:
        total_seconds = int(split_numbers(lines[telapse_line].split("TELAPSE")[1])[0])
        # m, s = divmod(total_seconds, 60)
        # h, m = divmod(m, 60)
        # elapsed_time = "%d:%02d:%02d" % (h, m, s)

    if not found_endprop:
        # TODO separate exit code?
        parser_errors.append("No ENDPROP found in stdout")

    return errors, warnings, parser_errors, total_seconds, start_lines


def parse_calculation_inputs(lines, initial_lineno):
    data = {}
    found_end = False
    for i, line in enumerate(lines[initial_lineno:]):
        if line.strip().startswith("NUMBER OF K POINTS IN THE IBZ"):
            found_end = True
            break
    final_lineno = initial_lineno + i + 1
    if not found_end:
        return ParsedSection(
            final_lineno, data, "couldn't find end of calculation setup"
        )

    # parse input system information
    content = "\n".join(lines[initial_lineno:final_lineno])
    for name, regex in list(SYSTEM_INFO_REGEXES) + list(INPUT_WF_REGEXES):
        match = regex.search(content)
        if match is not None:
            if name == "k_points":
                data["k_points"] = [int(match.groups()[i]) for i in range(3)]
            elif name.startswith("energy"):
                data[name] = convert_units(float(match.groups()[0]), "hartree", "eV")
            else:
                data[name] = int(match.groups()[0])

    return ParsedSection(final_lineno, data, None)


def parse_newk_params(lines, initial_lineno):
    """Parse NEWK calculation section.

    Example::

        *******************************************************************************
        RESTART WITH NEW K POINTS NET
        *******************************************************************************
        POINTS IN THE IBZ                 195 POINTS(GILAT NET)              1240
        SHRINK FACTORS(MONK.)        18 18 18 SHRINK FACTOR(GILAT)             36
        *******************************************************************************
        *** K POINTS COORDINATES (OBLIQUE COORDINATES IN UNITS OF IS = 18)
    """
    data = {}

    # parse newk information
    content = "\n".join(lines[initial_lineno:])

    for name, regex in NEWK_WF_REGEXES:
        match = regex.search(content)
        if match is not None:
            if name == "k_points":
                data["k_points"] = [int(match.groups()[i]) for i in range(3)]
            else:
                data[name] = int(match.groups()[0])

    return ParsedSection(initial_lineno, data, None)
