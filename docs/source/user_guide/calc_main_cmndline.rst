.. _main_calculation_cmndline:

Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~

Example Script Execution
------------------------

An example script is available within the
`examples folder <https://github.com/chrisjsewell/aiida-crystal17/tree/master/examples>`_.
You also either need to have the ``runcry17`` executable
available locally or set the global variable
``export MOCK_EXECUTABLES=true`` (to use a dummy executable).
Then, assuming AiiDA is configured and your database is running,
the script can be run within a terminal:

.. code:: shell

  >> verdi daemon start         # make sure the daemon is running
  >> cd examples
  >> verdi run test_submit_main.py       # submit test calculation
  submitted calculation; calc=Calculation(PK=1)
  >> verdi calculation list -a  # check status of calculation
    PK  Creation    State           Sched. state    Computer       Type
  ----  ----------  --------------  -------------  --------------  -----------------
  1     1m ago      WITHSCHEDULER   RUNNING        localhost-test  crystal17.main
  >> verdi calculation list -a  # after completion (~30 minutes if using runcry17)
    PK  Creation    State           Sched. state    Computer       Type
  ----  ----------  --------------  -------------  --------------  -----------------
  1     4m ago      FINISHED        DONE           localhost-test  crystal17.main

Once the calculation has run, it will be linked to the input nodes and a
number of output nodes:

.. code:: shell

  verdi calculation show 1
  -----------  ---------------------------------------------------
  type         CryMainCalculation
  pk           1
  uuid         3d9f804b-84db-443a-b6f8-69c15d96d244
  label        aiida_crystal17 test
  description  Test job submission with the aiida_crystal17 plugin
  ctime        2018-08-27 15:23:38.670705+00:00
  mtime        2018-08-27 15:24:26.516127+00:00
  computer     [1] localhost-test
  code         runcry17
  -----------  ---------------------------------------------------
  ##### INPUTS:
  Link label      PK  Type
  ------------  ----  -------------
  parameters    4     ParameterData
  settings      5     StructSettingsData
  basis_Ni      2     BasisSetData
  basis_O       3     BasisSetData
  structure     6     StructureData
  ##### OUTPUTS:
  Link label           PK  Type
  -----------------  ----  -------------
  remote_folder      7     RemoteData
  retrieved          8     FolderData
  output_parameters  9     ParameterData
  output_structure   10    StructureData
  ##### LOGS:
  There are 1 log messages for this calculation
  Run 'verdi calculation logshow 1' to see them

The inputs represent:

-  ``parameters`` is a dictionary of (structure independent) data,
    used to create the main.d12 file.
-  ``structure`` stores the initial atomic configuration for the calculation.
-  ``settings`` stores additional data related to the initial atomic
    configuration, such as symmetry operations and initial spin.
-  `basis_` store the basis set for each element

The outputs represent:

-  ``remote_folder`` provides a symbolic link to the work directory
   where the computation was run.
-  ``retrieved`` stores a folder containing the full stdout of
   ``runcry17`` (as main.out)
-  ``output_parameters`` stores a dictionary of key parameters in the
   database, for later querying.
-  ``output_structure`` stores the final geometry from the calculation

Input and Output Parameters
---------------------------

Both can be viewed at the command line:

.. code:: shell

  >> verdi data parameter show 4
  {
  "geometry": {
    "optimise": {
      "type": "FULLOPTG"
    }
  }, 
  "scf": {
    "k_points": [
      8, 
      8
    ], 
    "numerical": {
      "FMIXING": 30
    }, 
    "post_scf": [
      "PPAN"
    ], 
    "single": "UHF", 
    "spinlock": {
      "SPINLOCK": [
        0, 
        15
      ]
    }
  },
  "title": "NiO Bulk with AFM spin"
  }


For compatibility, output parameters are named
with the same convention as in :ref:`aiida-quantumespresso.pw <my-ref-to-pw-tutorial>`

.. code:: shell

    >> verdi data parameter show 9
    {
      "calculation_spin": true,
      "calculation_type": "unrestricted open shell",
      "ejplugins_version": "0.9.7",
      "energy": -85124.8936673389,
      "energy_units": "eV",
      "errors": [],
      "mulliken_spin_total": 0.0,
      "mulliken_spins": [
        3.057,
        -3.057,
        -0.072,
        0.072
      ],
      "number_of_assymetric": 4,
      "number_of_atoms": 4,
      "number_of_symmops": 16,
      "parser_class": "CryBasicParser",
      "parser_version": "0.2.0a0",
      "parser_warnings": [],
      "scf_iterations": 13,
      "volume": 36.099581472,
      "wall_time_seconds": 187,
      "warnings": []
    }

Input and Output Structures
---------------------------

The structures can be directly opened by a number of different
programs (assuming the executables are available):

.. code:: shell

   >> verdi data structure show --format xcrysden 10

.. note::

  The output structure will only be present for optimisations,
  and not SCF computations, i.e. only when the input structure
  has changed

Structure Settings Data
-----------------------

This node contains data to create the main.d12,
which is specific to the structure:

.. code:: shell

  >> verdi data cry17-settings show -symmetries 5
  centring_code:       1
  computation_class:   Symmetrise3DStructure
  computation_version: 0.3.0a0
  crystal_type:        4
  kinds:
    spin_alpha: [Ni1]
    spin_beta:  [Ni2]
  operations:          [[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0,
                      0.0], [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 1.0,
                      6.6613e-16, 0.0], [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0,
                      1.0, 2.2204e-16, 4.4409e-16, 0.0], [0.0, 1.0, 0.0, -1.0,
                      0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 2.2204e-16, 6.163e-33],
                      [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0, 1.0,
                      6.6613e-16, 0.0], [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
                      -1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0,
                      0.0, 1.0, 1.0, 2.2204e-16, 6.163e-33], [0.0, -1.0, 0.0,
                      1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 2.2204e-16, 4.4409e-16,
                      0.0], [1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0,
                      6.6613e-16, 0.0], [-1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
                      1.0, 1.0, 0.0, 0.0], [0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0,
                      0.0, -1.0, 2.2204e-16, 2.2204e-16, 0.0], [0.0, 1.0, 0.0,
                      1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 4.4409e-16, 6.163e-33],
                      [-1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0,
                      0.0], [1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0,
                      6.6613e-16, 0.0], [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0,
                      -1.0, 1.0, 4.4409e-16, 6.163e-33], [0.0, -1.0, 0.0, -1.0,
                      0.0, 0.0, 0.0, 0.0, 1.0, 2.2204e-16, 2.2204e-16, 0.0]]
  space_group:         123
  symmetry_program:    spglib
  symmetry_version:    1.9.10

In this case the symmetry operations, have been pre computed
by the :py:class:`~.Symmetrise3DStructure` workflow,
which will be discussed in :ref:`main_calculation_python`.

Basis Sets
----------

Basis sets are stored as individual nodes:

.. code:: shell

  >> verdi data cry17-basis show -c 2
  atomic_number: 28
  author:        John Smith
  basis_type:    all-electron
  class:         sto3g
  element:       Ni
  filename:      sto3g_Ni.basis
  md5:           fd341c4056cffcbd63ab92a94dea80e4
  num_shells:    5
  year:          1999
  28 5
  1 0 3  2.  0.
  1 1 3  8.  0.
  1 1 3  8.  0.
  1 1 3  2.  0.
  1 3 3  8.  0.

They can also (preferably) be grouped into families:

.. code:: shell

  >> verdi data cry17-basis listfamilies
  Family      Num Basis Sets
  --------  ----------------
  sto3g                    3

Families can be created from a folder of individual basis set files,
optionally with a yaml meta-data header (see :ref:`main_calc_python_basis`):

.. code:: shell

  >> verdi data cry17-basis uploadfamily --help
  Usage: verdi data cry17-basis uploadfamily [OPTIONS]

    Upload a family of CRYSTAL Basis Set files.

  Options:
    --path PATH             Path to a folder containing the Basis Set files
    --ext TEXT              the file extension to filter by
    --name TEXT             Name of the BasisSet family  [required]
    -D, --description TEXT  A description for the family
    --stop-if-existing      Abort when encountering a previously uploaded Basis
                            Set file
    --dry-run               do not commit to database or modify configuration
                            files
    --help                  Show this message and exit.



