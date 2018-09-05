========================
Main Calculation Plugin
========================

The ``crystal17.main`` plugin is designed with a more programmatic
input interface. It creates the input .d12 and .gui files,
from a set of AiiDa nodes (:py:class:`~.StructureData` and (:py:class:`~.ParameterData`). 

The structure mirrors closely that of :py:mod:`aiida_quantumespresso.calculations.pw`, 
which is discussed in `this tutorial <https://aiida-quantumespresso.readthedocs.io/en/latest/user_guide/get_started/examples/pw_tutorial.html>`_. 

This chapter will show how to launch a single CRYSTAL17 calculation.
We will look at how to run a computation *via* the terminal,
then how to construct the inputs for a computation in Python.
It is assumed that you have already performed the installation,
and that you already set up a computer (with verdi),
installed CRYSTAL17 and the ``runcry17`` executable on the cluster and in AiiDA.
Although the code should be quite readable,
a basic knowledge of Python and object programming is useful.

Command Line Example
~~~~~~~~~~~~~~~~~~~~~

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
  submitted calculation; calc=Calculation(PK=5)
  >> verdi calculation list -a  # check status of calculation
    PK  Creation    State           Sched. state    Computer       Type
  ----  ----------  --------------  -------------  --------------  -----------------
  7     1m ago      WITHSCHEDULER   RUNNING        localhost-test  crystal17.main
  >> verdi calculation list -a  # after completion (a few minutes if using runcry17)
    PK  Creation    State           Sched. state    Computer       Type
  ----  ----------  --------------  -------------  --------------  -----------------
  7     4m ago      FINISHED        DONE           localhost-test  crystal17.main

Once the calculation has run, it will be linked to the input nodes and a
number of output nodes:

.. code:: shell

  verdi calculation show 2267
  -----------  ---------------------------------------------------
  type         CryMainCalculation
  pk           7
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
  settings      5     ParameterData
  basis_Ni      2     BasisSetData
  basis_O       3     BasisSetData
  structure     6     StructureData
  ##### OUTPUTS:
  Link label           PK  Type
  -----------------  ----  -------------
  remote_folder      7     RemoteData
  retrieved          8     FolderData
  output_parameters  9     ParameterData
  output_arrays      10    ArrayData
  output_structure   11    StructureData
  ##### LOGS:
  There are 1 log messages for this calculation
  Run 'verdi calculation logshow 7' to see them

The outputs represent:

-  ``remote_folder`` provides a symbolic link to the work directory
   where the computation was run.
-  ``retrieved`` stores a folder containing the full stdout of
   ``runcry17`` (as main.out)
-  ``output_parameters`` stores a dictionary of key parameters in the
   database, for later querying.
-  ``output_arrays`` stores keys in the database to array data stored on file
   (such as symmetry operations and mulliken charges).
-  ``output_structure`` stores the final geometry from the calculation

For compatibility, parameters are named 
with the same convention as in :py:mod:`aiida_quantumespresso.parsers.basicpw`:

.. code:: shell

    >> verdi data parameter show 8
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

The final structure can be directly viewed by a number of different
programs (assuming the executables are available):

.. code:: shell

   >> verdi data structure show --format xcrysden 11

Input Components Creation
~~~~~~~~~~~~~~~~~~~~~~~~~

Within this demonstration we will show how to use the input nodes
can be used to create the following CRYSTAL17 input 
(and associated external geometry):

::

  NiO Bulk with AFM spin
  EXTERNAL
  END
  28 5
  1 0 3  2.  0.
  1 1 3  8.  0.
  1 1 3  8.  0.
  1 1 3  2.  0.
  1 3 3  8.  0.
  8 2
  1 0 3  2.  0.
  1 1 3  6.  0.
  99 0
  END
  UHF
  SHRINK
  8 8
  ATOMSPIN
  2
  1 1
  2 -1
  FMIXING
  30
  SPINLOCK
  0 15
  PPAN
  END

In the old way, not only you had to prepare 'manually' this file, but also prepare the scheduler submission script, send everything on the cluster, etc.
We are going instead to prepare everything in a more programmatic way.

We decompose this script into:

1. ``parameters`` containing aspects of the input which are independent of the geometry.
2. ``structure`` defining the geometry and species of the unit cell
3. ``settings`` defining how the geometry is to be modified and species specific data (such as spin)
4. ``basis_sets`` defining the basis set for each atomic type

Setting the Parameters
----------------------

The ``parameter`` input data defines the content in the
.d12 input file, which is independent of the geometry.

.. code-block:: python

  params = {'scf': {'k_points': (8, 8),
                    'numerical': {'FMIXING': 30},
                    'post_scf': ['PPAN'],
                    'single': 'UHF',
                    'spinlock': {'SPINLOCK': (0, 15)}},
            'title': 'NiO Bulk with AFM spin'}

The only mandated key is ``k_points`` (known as ``SHRINK`` in CRYSTAL17), 
and the full range of allowed keys, and their validation, is available in the
`inputd12.schema.json <https://github.com/chrisjsewell/aiida-crystal17/tree/master/aiida_crystal17/validation/inputd12.schema.json>`_.
Which can be used programmatically:

.. code:: Python

  from aiida_crystal17.validation import read_schema, validate_dict
  read_schema("inputd12")
  validate_dict(params, "inputd12")

The dictionary can also be written in a flattened manner, delimited by '.',
and subsequently converted:

.. code:: Python

  params = {
        "title": "NiO Bulk with AFM spin",
        "scf.single": "UHF",
        "scf.k_points": (8, 8),
        "scf.spinlock.SPINLOCK": (0, 15),
        "scf.numerical.FMIXING": 30,
        "scf.post_scf": ["PPAN"]
    }

  from aiida_crystal17.utils import unflatten_dict
  params = unflatten_dict(params)

This dictionary is used to create the outline of the .d12 file:

.. code:: Python

  >>> from aiida_crystal17.parsers.inputd12 import write_input
  >>> write_input(params, ["<basis sets>"])
  NiO Bulk with AFM spin
  EXTERNAL
  END
  <basis sets>
  99 0
  END
  UHF
  SHRINK
  8 8
  FMIXING
  30
  SPINLOCK
  0 15
  PPAN
  END

Here is a relatively exhaustive parameter dictionary,
of the keys implemented thus far:

.. code:: Python

  params = {
      "title": "a title",
      "geometry": {
          "info_print": ["ATOMSYMM", "SYMMOPS"],
          "info_external": ["STRUCPRT"],
          "optimise": {
              "type": "FULLOPTG",
              "hessian": "HESSIDEN",
              "gradient": "NUMGRATO",
              "info_print": ["PRINTOPT", "PRINTFORCES"],
              "convergence": {
                  "TOLDEG": 0.0003,
                  "TOLDEX": 0.0012,
                  "TOLDEE": 7,
                  "MAXCYCLE": 50,
                  "FINALRUN": 4
              },
          }
      },
      "basis_set": {
          "CHARGED": False,
      },
      "scf": {
          "dft": {
              "xc": ["LDA", "PZ"],
              # or
              # "xc": "HSE06",
              # or
              # "xc": {"LSRSH-PBE": [0.11, 0.25, 0.00001]},
              "SPIN": True,
              "grid": "XLGRID",
              "grid_weights": "BECKE",
              "numerical": {
                  "TOLLDENS": 6,
                  "TOLLGRID": 14,
                  "LIMBEK": 400
              }
          },
          # or
          # "single": "UHF",
          "k_points": [8, 8],
          "numerical": {
              "BIPOLAR": [18, 14],
              "BIPOSIZE": 4000000,
              "EXCHSIZE": 4000000,
              "EXCHPERM": False,
              "ILASIZE": 6000,
              "INTGPACK": 0,
              "MADELIND": 50,
              "NOBIPCOU": False,
              "NOBIPEXCH": False,
              "NOBIPOLA": False,
              "POLEORDR": 4,
              "TOLINTEG": [6, 6, 6, 6, 12],
              "TOLPSEUD": 6,
              "FMIXING": 0,
              "MAXCYCLE": 50,
              "TOLDEE": 6,
              "LEVSHIFT": [2, 1],
              "SMEAR": 0.1
          },
          "fock_mixing": "DIIS",
          # or
          # "fock_mixing": {"BROYDEN": [0.0001, 50, 2]},
          "spinlock": {
              "SPINLOCK": [1, 10]
          },
          "post_scf": ["GRADCAL", "PPAN"]
      }
  }

Structure and Settings
----------------------

The ``structure`` refers to a standard :py:class:`~.StructureData` node in AiiDa.

Basis Sets
----------

Basis sets are stored as separate :py:class:`~.BasisSetData` nodes,
in a similar fashion to :py:class:`~.UpfData`.
They are created individually from a text file,
which contains the content of the basis set
and (optionally) a yaml style header section, fenced by '---':

.. code:: text

  ---
  author: John Smith
  year: 1999
  class: sto3g
  ---
  12 3
  1 0 3  2.  0.
  1 1 3  8.  0.
  1 1 3  2.  0.

.. code:: python

  >>> import os
  >>> import aiida_crystal17.tests as tests
  >>> fpath = os.path.join(tests.TEST_DIR, "input_files", "sto3g", "sto3g_Mg.basis")

  >>> from aiida.orm import DataFactory
  >>> BasisSetData = DataFactory("crystal17.basisset")
  >>> bset, created = BasisSetData.get_or_create(fpath)
  >>> bset.metadata
  {
    'num_shells': 3,
    'author': 'John Smith',
    'atomic_number': 12,
    'filename': 'sto3g_Mg.basis',
    'element': 'Mg',
    'year': 1999,
    'basis_type': 'all-electron',
    'class': 'sto3g',
    'md5': '0731ecc3339d2b8736e61add113d0c6f'
  }

The attributes of the basis set are stored in the database, 
and the md5 hash-sum is used to test equivalence of two basis sets.

A simpler way to create and refer to basis sets, is *via* a family group.
All basis sets in a folder can be read and saved to a named family by:

.. code:: python

  >>> from aiida_crystal17.data.basis_set import upload_basisset_family
  >>> nfiles, nuploaded = upload_basisset_family(
          os.path.join(tests.TEST_DIR, "input_files", "sto3g"), 
          "sto3g", "group of sto3g basis sets",
          extension=".basis")

The basis sets for a particular structure are then extracted by

.. note:: 

  Unlike :py:mod:`aiida_quantumespresso.calculations.pw`,
  the basis sets are defined per atomic number only **NOT** per species kind.
  This is because, using multiple basis set per atomic number is rarely used in CRYSTAL17.