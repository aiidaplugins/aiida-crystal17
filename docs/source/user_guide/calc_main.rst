.. _main_calculation_plugin:

========================
Main Calculation Plugin
========================

The ``crystal17.main`` plugin is designed with a more programmatic
input interface. It creates the input ``.d12`` and ``.gui`` files,
from a set of AiiDa nodes (
:py:class:`~aiida.orm.data.structure.StructureData` and
:py:class:`~aiida.orm.data.parameter.ParameterData`).

.. note::

  The approach mirrors closely that of the ``aiida-quantumespresso.pw`` plugin,
  which is discussed in :ref:`this tutorial <my-ref-to-pw-tutorial>`

This chapter will show how to launch a single CRYSTAL17 calculation.
We will look at how to run a computation *via* the terminal,
then how to construct the inputs for a computation in Python.
It is assumed that you have already performed the installation,
and that you already set up a computer (with verdi),installed CRYSTAL17
and the ``runcry17`` executable on the cluster and in AiiDA.
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
   (such as symmetry operations and Mulliken charges).
-  ``output_structure`` stores the final geometry from the calculation

For compatibility, parameters are named
with the same convention as in :ref:`aiida-quantumespresso.pw <my-ref-to-pw-tutorial>`

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

Creation and Execution Walk-through
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

In the old way, not only you had to prepare 'manually' this file, but also
prepare the scheduler submission script, send everything on the cluster, etc.
We are going instead to prepare everything in a more programmatic way.

We decompose this script into:

1. ``parameters`` containing aspects of the input which are independent of the geometry.
2. ``structure`` defining the geometry and species of the unit cell
3. ``settings`` defining how the geometry is to be modified and species specific data (such as spin)
4. ``basis_sets`` defining the basis set for each atomic type

Parameters
----------

The ``parameter`` input data defines the content in the
``.d12`` input file, that is **independent of the geometry**.
It follows the naming convention and structure
described in the `CRYSTAL17 Manual <http://www.crystal.unito.it/Manuals/crystal17.pdf>`_.

.. code-block:: python

  params = {'scf': {'k_points': (8, 8),
                    'numerical': {'FMIXING': 30},
                    'post_scf': ['PPAN'],
                    'single': 'UHF',
                    'spinlock': {'SPINLOCK': (0, 15)}},
            'title': 'NiO Bulk with AFM spin'}

  from aiida.orm import DataFactory
  ParameterData = DataFactory('parameter')

  parameters = ParameterData(dict=params)

The only mandated key is ``k_points`` (known as ``SHRINK`` in CRYSTAL17),
and the full range of allowed keys, and their validation, is available in the
`inputd12.schema.json <https://github.com/chrisjsewell/aiida-crystal17/tree/master/aiida_crystal17/validation/inputd12.schema.json>`_,
which can be used programmatically:

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

Structure
---------

The ``structure`` refers to a standard
:py:class:`~aiida.orm.data.structure.StructureData` node in AiiDa.
We now proceed in setting up the structure.

.. note:: Here we discuss only the main features of structures in AiiDA, needed
    to run a CRYSTAL17 calculation.

    For more detailed information, have a look to the
    :ref:`AiiDa Tutorial <structure_tutorial>` or
    :ref:`QuantumEspresso Tutorial <my-ref-to-pw-tutorial>`.

Structures consist of:

- A cell with a basis vectors and whether it is periodic, for each dimension
- ``Site`` with a cartesian coordinate and reference to a kind
- ``Kind`` which details the species and composition at one or more sites

The simplest way to create a structure is *via* :py:mod:`ase`:

.. code:: python

  from ase.spacegroup import crystal

  atoms = crystal(
    symbols=[28, 8],
    basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
    spacegroup=225,
    cellpar=[4.164, 4.164, 4.164, 90, 90, 90])

  from aiida.orm import DataFactory
  StructureData = DataFactory('structure')

  structure = StructureData(ase=atoms)

As default, one kind is created per atomic species
(named as the atomic symbol):

.. code:: python

  >>> structure.get_site_kindnames()
  ['Ni', 'Ni', 'Ni', 'Ni', 'O', 'O', 'O', 'O']

However, we may want to specify more than one kind per species
(for example to setup anti-ferromagnetic spin).
We can achieve this by tagging the atoms:

.. code:: python

  >>> atoms_afm = atoms.copy()
  >>> atoms_afm.set_tags([1, 1, 2, 2, 0, 0, 0, 0])
  >>> structure = StructureData(ase=atoms_afm)
  >>> structure.get_site_kindnames()
  ['Ni1', 'Ni1', 'Ni2', 'Ni2', 'O', 'O', 'O', 'O']

Settings
--------

Since we **always** use the ``EXTERNAL`` keyword for geometry,
any manipulation to the geometry is undertaken before calling CRYSTAL
(i.e. we delegate the responsibility for geometry away from CRYSTAL).
Also, we may want to add atom specific inputs to the ``.d12``
(such as spin).

The ``settings`` parameters are used to define some key aspects
of the atomic configurations:

1. Properties by ``Kind``
2. Any pre-processing of the geometry
3. The input symmetry operations

Available parameters for the settings dictionary are defined
(and validated by) the
`settings.schema.json <https://github.com/chrisjsewell/aiida-crystal17/tree/master/aiida_crystal17/validation/settings.schema.json>`_.
The ``crystal17.main`` calculation defines a default specification:

.. code:: python

  >>> from aiida.orm import CalculationFactory
  >>> calc_cls = CalculationFactory('crystal17.main')
  >>> calc_cls.default_settings
  {
    'kinds': {
      'fixed': [],
      'ghosts': [],
      'spin_alpha': [],
      'spin_beta': []
    },
    'symmetry': {
      'sgnum': 1,
      'operations': None,
      'symprec': 0.01,
      'angletol': None
    },
    'crystal': {
      'system': 'triclinic',
      'transform': None
    },
    '3d': {
      'standardize': True,
      'primitive': True,
      'idealize': False
    }
  }

Properties by Kind
..................

The `kinds` lists can be populated by kind names.
For example, for a stucture with kinds:
``['Ni1', 'Ni1', 'Ni2', 'Ni2', 'O', 'O', 'O', 'O', 'S']``,
if the kinds settings are:

.. code:: python

  {
    'kinds': {
        'fixed': ['O'],
        'ghosts': ['S'],
        'spin_alpha': ['Ni1'],
        'spin_beta': ['Ni2']
    }
  }

Then the ``main.d12`` would contain
(assuming we do not create a primitive cell);

::

  FRAGMENT
  8
  1 2 3 4 5 6 7 8

in the ``OPTGEOM`` block (specifying atoms free to move),

::

  GHOSTS
  1
  9

In the ``BASIS SET`` block (specifying atoms which are removed,
but their basis sets left), and

::

  ATOMSPIN
  1 1 2 1 3 1 4 1 5 -1 6 -1 7 -1 8 -1

In the ``HAMILTONIAN`` block (specifying initial spin state)


Symmetry
........

In the ``main.gui`` file,
as well as using the dimensionality (i.e. periodic boundary conditions),
basis vectors and atomic positions, provided by the ``structure``,
we also need to specify the symmetry operators, and (optionally)
the crystal system and primitive-to-crystallographic transform
(referred to as the ``CENTRING CODE`` in ``CRYSTAL``).

The first option is to provide them directly:

.. code:: python

  {
    'symmetry': {
      'sgnum': 2,
      'operations': [
        [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        [-1, 0, 0, 0, -1, 0, 0, 0, -1, 0, 0, 0]
     ]
    },
    'crystal': {
      'system': 'triclinic',
      'transform': 1
    }
  }

The ``operations`` are given as a flattened version of the rotation matrix,
followed by the translation vector, in cartesian coordinates.

Alternatively, if ``operations`` is left as ``None``,
the space group and symmetry operators can be computed internally,
*via* the `spglib <https://atztogo.github.io/spglib/>`_ library.

.. important::

  Symmetry computations are based on atomic number **AND** kind.

So, for example, taking our structure with kinds;

::

  ['Ni', 'Ni', 'Ni', 'Ni', 'O', 'O', 'O', 'O']

.. code:: python

  >>> settings = {'3d': {'idealize': False, 'primitive': False, 'standardize': False},
  ... 'crystal': {'system': 'triclinic', 'transform': None},
  ... 'kinds': {'fixed': [], 'ghosts': [], 'spin_alpha': [], 'spin_beta': []},
  ... 'symmetry': {'angletol': None, 'operations': None, 'symprec': 0.01}}

  >>> from aiida_crystal17.parsers.geometry import compute_symmetry_from_ase
  >>> new_atoms, symdata = compute_symmetry_from_ase(atoms, settings)
  >>> len(symdata["symops"])
  192
  >>> symdata["sgnum"]
  225

Whereas, for the structure with multiple Ni kinds;

::

  ['Ni1', 'Ni1', 'Ni2', 'Ni2', 'O', 'O', 'O', 'O']

.. code:: python

  >>> new_atoms, symdata = compute_symmetry_from_ase(atoms_afm, settings)
  >>> len(symdata["symops"])
  32
  >>> symdata["sgnum"]
  123

Finally, CRYSTAL expects the geometry in a standardized form,
which minimises the translational symmetry components.
For 3d structures (2d to come), the structure can be converted to a standardized,
and (optionally) primitive cell:

.. code:: python

  >>> settings = {'3d': {'idealize': False, 'primitive': True, 'standardize': True},
  ... 'crystal': {'system': 'triclinic', 'transform': None},
  ... 'kinds': {'fixed': [], 'ghosts': [], 'spin_alpha': [], 'spin_beta': []},
  ... 'symmetry': {'angletol': None, 'operations': None, 'symprec': 0.01}}

  >>> from aiida_crystal17.parsers.geometry import compute_symmetry_from_ase
  >>> new_atoms, symdata = compute_symmetry_from_ase(atoms, settings)
  >>> new_atoms.get_chemical_formula()
  'NiO'
  >>> symdata["centring_code"]
  5

.. code:: python

  >>> new_atoms, symdata = compute_symmetry_from_ase(atoms_afm, settings)
  >>> new_atoms.get_chemical_formula()
  'Ni2O2'
  >>> symdata["centring_code"]
  1

The other option is to ``idealize`` the structure, which
removes distortions of the unit cell's atomic positions,
compared to the ideal symmetry.

Basis Sets
----------

Basis sets are stored as separate :py:class:`~.BasisSetData` nodes,
in a similar fashion to :py:class:`~aiida.orm.data.upf.UpfData`
(discussed in :ref:`this tutorial <my-ref-to-pseudo-tutorial>` ).
They are created individually from a text file,
which contains the content of the basis set
and (optionally) a yaml style header section, fenced by ``---``:

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

Basis families can be searched (optionally by the elements they contain):

.. code:: python

  >>> from aiida.orm import DataFactory
  >>> basis_cls = DataFactory('crystal17.basisset')
  >>> basis_cls.get_basis_groups(["Ni", "O"])
  [<Group: "sto3g" [type data.basisset.family], of user test@hotmail.com>]

The basis sets for a particular structure
are then extracted by ``crystal17.main``:

.. code:: python

  >>> from ase.spacegroup import crystal

  >>> atoms = crystal(
  ...   symbols=[28, 8],
  ...   basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
  ...   spacegroup=225,
  ...   cellpar=[4.164, 4.164, 4.164, 90, 90, 90])

  >>> from aiida.orm import DataFactory
  >>> StructureData = DataFactory('structure')

  >>> structure = StructureData(ase=atoms)

  >>> from aiida_crystal17.data.basis_set import get_basissets_from_structure
  >>> get_basissets_from_structure(structure, "sto3g", by_kind=False)
  {'Ni': <BasisSetData: uuid: d1529498-1cc4-48cc-9524-42355e7a6f18 (pk: 2320)>,
  'O': <BasisSetData: uuid: 67d87176-cb83-4082-be06-8dae80c488c3 (pk: 2321)>}

.. important::

  Unlike :ref:`aiida-quantumespresso.pw <my-ref-to-pw-tutorial>`,
  ``crystal17.main`` uses one basis sets per atomic number only **NOT** per kind.
  This is because, using multiple basis sets per atomic number is rarely used in CRYSTAL17,
  and is limited anyway to only two types per atomic number.

.. todo::

  command line interface


Input Preparation and Validation
--------------------------------

Before creating and submitting the calculation,
:py:class:`~.CryMainCalculation` provides a helper function,
to prepare the parameter and settings data
and validate their content.

.. code:: python

  from aiida.orm import DataFactory, CalculationFactory
  StructureData = DataFactory('structure')
  calc_cls = CalculationFactory('crystal17.main')

  atoms = crystal(
      symbols=[28, 8],
      basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
      spacegroup=225,
      cellpar=[4.164, 4.164, 4.164, 90, 90, 90])
  atoms.set_tags([1, 1, 2, 2, 0, 0, 0, 0])
  instruct = StructureData(ase=atoms)

  params = {
      "title": "NiO Bulk with AFM spin",
      "scf.single": "UHF",
      "scf.k_points": (8, 8),
      "scf.spinlock.SPINLOCK": (0, 15),
      "scf.numerical.FMIXING": 30,
      "scf.post_scf": ["PPAN"]
  }
  settings = {"kinds.spin_alpha": ["Ni1"],
              "kinds.spin_beta": ["Ni2"]}

  pdata, sdata = calc_cls.prepare_and_validate(params, instruct,
                                               settings=settings,
                                               basis_family="sto3g",
                                               flattened=True)

Creating and Submitting Calculation
-----------------------------------

As in the AiiDa tutorial :ref:`aiida:setup_code`
and the :ref:`qe.pw tutorial <my-ref-to-pw-tutorial>`,
to run the computation on a remote computer,
you will need to setup ``computer`` and ``code`` nodes.
Then the code can be submitted using ``verdi run`` or programmatically:

.. code:: python

  from aiida import load_dbenv
  load_dbenv()

  from aiida.orm import Code
  code = Code.get_from_string('cry17.2@MyHPC')
  calc = code.new_calc()

  calc.label = "aiida_crystal17 test"
  calc.description = "Test job submission with the aiida_crystal17 plugin"
  calc.set_max_wallclock_seconds(30)
  calc.set_withmpi(False)
  calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

  calc.use_parameters(pdata)
  calc.use_structure(instruct)
  calc.use_settings(sdata)
  calc.use_basisset_from_family("sto3g")

  calc.store_all()

  calc.submit()
