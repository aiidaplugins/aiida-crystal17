DOSS Calculation
++++++++++++++++

.. todo:: DOSS Calculation

.. note::

    More information to come...

The :py:class:`~.aiida_crystal17.calculations.cry_doss.CryDossCalculation` can be used to run the `properties`
executable for DOSS calculations, from an existing ``fort.9``.

.. nbinput:: ipython

    !verdi plugin list aiida.calculations crystal17.doss

.. nboutput::

    Inputs
               code:  required  Code           The Code to use for this job.
         parameters:  required  Dict           the input parameters to create the DOSS input file.
          wf_folder:  required  RemoteData     the folder containing the wavefunction fort.9 file
           metadata:  optional
    Outputs
      remote_folder:  required  RemoteData     Input files necessary to run the process will be stored in this folder node ...
            results:  required  Dict           summary of the parsed data
          retrieved:  required  FolderData     Files that are retrieved by the daemon will be stored in this node. By defa ...
             arrays:  optional  ArrayData      energies and DoS arrays
          structure:  optional  StructureData  the structure output from the calculation
           symmetry:  optional  SymmetryData   the symmetry data from the calculation
    Exit codes
                  1:  The process has failed with an unspecified error.
                  2:  The process failed with legacy failure mode.
                 10:  The process returned an invalid output.
                 11:  The process did not register a required output.
                200:  The retrieved folder data node could not be accessed.
                210:  The main (stdout) output file was not found
                211:  The temporary retrieved folder was not found
                300:  An error was flagged trying to parse the crystal exec stdout file
                301:  An error occurred parsing the 'opta'/'optc' geometry files
                302:  The crystal exec stdout file denoted that the run was a testgeom
                350:  The input file could not be read by crystal
                351:  Crystal could not find the required wavefunction file
                352:  Parser could not find the output isovalue (fort.25) file
                400:  The calculation stopped prematurely because it ran out of walltime.
                401:  The calculation stopped prematurely because it ran out of memory.
                402:  The calculation stopped prematurely because it ran out of virtual memory.
                411:  Scf convergence did not finalise (usually due to reaching step limit)
                412:  Geometry convergence did not finalise (usually due to reaching step limit)
                413:  An error encountered usually during geometry optimisation
                414:  An error was encountered during an scf computation
                415:  An unknown error was encountered, causing the mpi to abort
                499:  The main crystal output file flagged an unhandled error
                510:  Inconsistency in the input and output symmetry
                520:  Primitive symmops were not found in the output file


The :ref:`doss_input_schema` gives the allowed format of the input dictionary, for example:

.. nbinput:: python
    :no-output:

    from aiida.orm import Dict
    Dict(dict={
        "shrink_is": 18,
        "shrink_isp": 36,
        "npoints": 100,
        "band_minimum": -10,
        "band_maximum": 10,
        "band_units": "eV"
    })

.. _doss_projections:

Computing Projections
~~~~~~~~~~~~~~~~~~~~~

Projections can be added per atom or per orbital set:

.. nbinput:: python
    :no-output:

    Dict(dict={
        "shrink_is": 18,
        "shrink_isp": 36,
        "npoints": 100,
        "band_minimum": -10,
        "band_maximum": 10,
        "band_units": "eV",
        "atomic_projections": [0, 1],
        "orbital_projections": [[1, 2, 3]]
    })

.. note::

    A maximum of 15 projections are allowed per calculation.

In order to create orbital sets,
it is possible to compute the nature of each orbital,
using the atomic structure and basis sets used to create the ``fort.9``:

.. nbinput:: python

    from aiida_crystal17.tests import get_test_structure_and_symm
    from aiida_crystal17.symmetry import print_structure
    structure, _ = get_test_structure_and_symm('NiO_afm')
    print_structure(structure)

.. nboutput::

    StructureData Summary
    Lattice
        abc : 2.944 2.944 4.164
    angles :  90.0  90.0  90.0
    volume :  36.1
        pbc : True True True
          A : 2.944   0.0   0.0
          B :   0.0 2.944   0.0
          C :   0.0   0.0 4.164
    Kind  Symbols Position
    ----  ------- --------
    Ni1   Ni      0.0     0.0     0.0
    Ni2   Ni      1.472   1.472   2.082
    O     O       0.0     0.0     2.082
    O     O       1.472   1.472   0.0

.. nbinput:: python

    from aiida.plugins import DataFactory
    basis_cls = DataFactory('crystal17.basisset')
    basis_sets = basis_cls.get_basissets_from_structure(structure, 'sto3g')
    basis_data = {k: v.get_data() for k, v in basis_sets.items()}
    basis_data

.. nboutput::

    {'Ni': {'type': 'all-electron',
      'bs': [{'type': 'S', 'functions': ['STO-nG(nd) type 3-21G core shell']},
      {'type': 'SP', 'functions': ['STO-nG(nd) type 3-21G core shell']},
      {'type': 'SP', 'functions': ['STO-nG(nd) type 3-21G core shell']},
      {'type': 'SP', 'functions': ['STO-nG(nd) type 3-21G core shell']},
      {'type': 'D', 'functions': ['STO-nG(nd) type 3-21G core shell']}]},
     'O': {'type': 'all-electron',
      'bs': [{'type': 'S', 'functions': ['STO-nG(nd) type 3-21G core shell']},
      {'type': 'SP', 'functions': ['STO-nG(nd) type 3-21G core shell']}]}}

.. nbinput:: python

    from aiida_crystal17.parsers.raw.parse_bases import compute_orbitals
    result = compute_orbitals(structure.get_ase().numbers, basis_data)
    print("number of electrons: ", result.electrons)
    print("number of core electrons: ", result.core_electrons)
    result.ao_indices

.. nboutput::

    number of electrons:  72
    number of core electrons:  40
    { 1: {'atom': 0, 'element': 'Ni', 'type': 'S', 'index': 1},
      2: {'atom': 0, 'element': 'Ni', 'type': 'SP', 'index': 1},
      3: {'atom': 0, 'element': 'Ni', 'type': 'SP', 'index': 1},
      4: {'atom': 0, 'element': 'Ni', 'type': 'SP', 'index': 1},
      5: {'atom': 0, 'element': 'Ni', 'type': 'SP', 'index': 1},
      6: {'atom': 0, 'element': 'Ni', 'type': 'SP', 'index': 2},
      7: {'atom': 0, 'element': 'Ni', 'type': 'SP', 'index': 2},
      8: {'atom': 0, 'element': 'Ni', 'type': 'SP', 'index': 2},
      9: {'atom': 0, 'element': 'Ni', 'type': 'SP', 'index': 2},
      10: {'atom': 0, 'element': 'Ni', 'type': 'SP', 'index': 3},
      11: {'atom': 0, 'element': 'Ni', 'type': 'SP', 'index': 3},
      12: {'atom': 0, 'element': 'Ni', 'type': 'SP', 'index': 3},
      13: {'atom': 0, 'element': 'Ni', 'type': 'SP', 'index': 3},
      14: {'atom': 0, 'element': 'Ni', 'type': 'D', 'index': 1},
      15: {'atom': 0, 'element': 'Ni', 'type': 'D', 'index': 1},
      16: {'atom': 0, 'element': 'Ni', 'type': 'D', 'index': 1},
      17: {'atom': 0, 'element': 'Ni', 'type': 'D', 'index': 1},
      18: {'atom': 0, 'element': 'Ni', 'type': 'D', 'index': 1},
      19: {'atom': 1, 'element': 'Ni', 'type': 'S', 'index': 1},
      20: {'atom': 1, 'element': 'Ni', 'type': 'SP', 'index': 1},
      21: {'atom': 1, 'element': 'Ni', 'type': 'SP', 'index': 1},
      22: {'atom': 1, 'element': 'Ni', 'type': 'SP', 'index': 1},
      23: {'atom': 1, 'element': 'Ni', 'type': 'SP', 'index': 1},
      24: {'atom': 1, 'element': 'Ni', 'type': 'SP', 'index': 2},
      25: {'atom': 1, 'element': 'Ni', 'type': 'SP', 'index': 2},
      26: {'atom': 1, 'element': 'Ni', 'type': 'SP', 'index': 2},
      27: {'atom': 1, 'element': 'Ni', 'type': 'SP', 'index': 2},
      28: {'atom': 1, 'element': 'Ni', 'type': 'SP', 'index': 3},
      29: {'atom': 1, 'element': 'Ni', 'type': 'SP', 'index': 3},
      30: {'atom': 1, 'element': 'Ni', 'type': 'SP', 'index': 3},
      31: {'atom': 1, 'element': 'Ni', 'type': 'SP', 'index': 3},
      32: {'atom': 1, 'element': 'Ni', 'type': 'D', 'index': 1},
      33: {'atom': 1, 'element': 'Ni', 'type': 'D', 'index': 1},
      34: {'atom': 1, 'element': 'Ni', 'type': 'D', 'index': 1},
      35: {'atom': 1, 'element': 'Ni', 'type': 'D', 'index': 1},
      36: {'atom': 1, 'element': 'Ni', 'type': 'D', 'index': 1},
      37: {'atom': 2, 'element': 'O', 'type': 'S', 'index': 1},
      38: {'atom': 2, 'element': 'O', 'type': 'SP', 'index': 1},
      39: {'atom': 2, 'element': 'O', 'type': 'SP', 'index': 1},
      40: {'atom': 2, 'element': 'O', 'type': 'SP', 'index': 1},
      41: {'atom': 2, 'element': 'O', 'type': 'SP', 'index': 1},
      42: {'atom': 3, 'element': 'O', 'type': 'S', 'index': 1},
      43: {'atom': 3, 'element': 'O', 'type': 'SP', 'index': 1},
      44: {'atom': 3, 'element': 'O', 'type': 'SP', 'index': 1},
      45: {'atom': 3, 'element': 'O', 'type': 'SP', 'index': 1},
      46: {'atom': 3, 'element': 'O', 'type': 'SP', 'index': 1}}


To observe DoS at the fermi level,
these results can also be used to choose a sensible range of bands:

.. nbinput:: python
    :no-output:

    filled_bands = int(result.electrons / 2)
    first_band = int(result.core_electrons / 2) + 1
    last_band = min([first_band + 2 * (filled_bands - first_band), result.number_ao])

    Dict(dict={
        "shrink_is": 18,
        "shrink_isp": 36,
        "npoints": 1000,
        "band_minimum": first_band,
        "band_maximum": last_band,
        "band_units": "bands"
    })
