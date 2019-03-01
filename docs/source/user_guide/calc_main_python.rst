.. _main_calculation_python:

Python API Walk-through
~~~~~~~~~~~~~~~~~~~~~~~

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
3. ``settings`` defining additional geometric and species specific data (such as spin)
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

  from aiida.plugins import DataFactory
  ParameterData = DataFactory('dict')

  parameters = ParameterData(dict=params)

The only mandated key is ``k_points`` (known as ``SHRINK`` in CRYSTAL17),
and the full range of allowed keys, and their validation, is available in the
`inputd12.schema.json <https://github.com/chrisjsewell/aiida-crystal17/tree/master/aiida_crystal17/validation/inputd12.schema.json>`_,
which can be used programmatically:

.. code:: Python

  from aiida_crystal17.validation import read_schema, validate_with_json
  read_schema("inputd12")
  validate_with_json(params, "inputd12")

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

  >>> from aiida_crystal17.parsers.inputd12_write import write_input
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

  from aiida.plugins import DataFactory
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
  >>> structure_afm = StructureData(ase=atoms_afm)
  >>> structure_afm.get_site_kindnames()
  ['Ni1', 'Ni1', 'Ni2', 'Ni2', 'O', 'O', 'O', 'O']

Structure Settings
------------------

Since we **always** use the ``EXTERNAL`` keyword for geometry,
any manipulation to the geometry is undertaken before calling CRYSTAL
(i.e. we delegate the responsibility for geometry away from CRYSTAL).
Also, we may want to add atom specific inputs to the ``.d12``
(such as spin).

The ``settings`` parameters are used to define some key aspects
of the atomic configurations:

1. Properties by ``Kind``
2. Crystallographic data for the geometry
3. The input symmetry operations

Available validation schema for the settings data 
can be viewed programattically at
:py:attr:`~.StructSettingsData.data_schema`

Or *via* the command line:

.. code:: shell

  >>> verdi data cry17-settings schema
  $schema:              http://json-schema.org/draft-04/schema#
  additionalProperties: False
  properties:           
    centring_code: 
      description: The crystal type, as designated by CRYSTAL17
      maximum:     6
      minimum:     1
      type:        integer
    computation_class: 
      description: the class used to compute the settings
      type:        string
    computation_version: 
      description: the version of the class used to compute the settings
      type:        string
    crystal_type: 
      description: The crystal type, as designated by CRYSTAL17
      maximum:     6
      minimum:     1
      type:        integer
    kinds: 
      additionalProperties: False
      description:          settings for input properties of each species kind
      properties:           
        fixed: 
          description: kinds with are fixed in position for optimisations (set by
                      FRAGMENT)
          items:       
            type:        string
            uniqueItems: True
          type:        array
        ghosts: 
          description: kinds which will be removed, but their basis set are left
                      (set by GHOSTS)
          items:       
            type:        string
            uniqueItems: True
          type:        array
        spin_alpha: 
          description: kinds with initial alpha (+1) spin (set by ATOMSPIN)
          items:       
            type:        string
            uniqueItems: True
          type:        array
        spin_beta: 
          description: kinds with initial beta (-1) spin (set by ATOMSPIN)
          items:       
            type:        string
            uniqueItems: True
          type:        array
      type:                 object
    operations: 
      description: symmetry operations to use (in the fractional basis)
      items:       
        description: each item should be a list of
                    [r00,r10,r20,r01,r11,r21,r02,r12,r22,t0,t1,t2]
        items:       
          maximum: 1
          minimum: -1
          type:    number
        maxItems:    12
        minItems:    12
        type:        array
      type:        [null, array]
    space_group: 
      description: Space group number (international)
      maximum:     230
      minimum:     1
      type:        integer
    symmetry_program: 
      description: the program used to generate the symmetry
      type:        string
    symmetry_version: 
      description: the version of the program used to generate the symmetry
      type:        string
  required:             [space_group, crystal_type, centring_code, operations]
  title:                CRYSTAL17 structure symmetry settings
  type:                 object



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
we also need to specify the symmetry operators, and
the crystal system and primitive-to-crystallographic transform
(referred to as the ``CENTRING CODE`` in ``CRYSTAL``).

These are provided by the ``crystal17.structsettings``:

.. code:: python

  {
    'space_group': 2,
    'operations': [
        [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        [-1, 0, 0, 0, -1, 0, 0, 0, -1, 0, 0, 0]
     ],
    'crystal_type': 1,
    'centring_code': 1
  }

.. note::

  The ``operations`` are given as a flattened version of the rotation matrix,
  followed by the translation vector, in **fractional** coordinates.

Pre-Processing of the Structure
-------------------------------

To compute the symmetry operations,
and optionally convert the structure to a standard primitive,
the space group and symmetry operators can be computed internally,
a pre-processing workflow has been created
(currently only for 3D-periodic structures),
:py:class:`~.Symmetrise3DStructure`,
which can be run with the helper function
:py:func:`~.run_symmetrise_3d_structure`.

This uses the `spglib <https://atztogo.github.io/spglib/>`_ library
to compute symmetries, but with the added constraint that sites
with the same ``Kind`` must be symmetrically equivalent.

.. important::

  Symmetrical equivalence is based on atomic number **AND** kind.

So, for example, taking our structure with kinds;

::

  ['Ni', 'Ni', 'Ni', 'Ni', 'O', 'O', 'O', 'O']

.. code:: python

  >>> settings_dict = {'primitive': False, 'standardize': False, 'idealize': False,
  ... 'kinds': {'fixed': [], 'ghosts': [], 'spin_alpha': [], 'spin_beta': []},
  ... 'angletol': None, 'symprec': 0.01}

  >>> from aiida_crystal17.workflows.symmetrise_3d_struct import run_symmetrise_3d_structure
  >>> newstruct, settings = run_symmetrise_3d_structure(structure, settings_dict)
  >>> settings.num_symops
  192
  >>> settings.space_group
  225

Whereas, for the structure with multiple Ni kinds;

::

  ['Ni1', 'Ni1', 'Ni2', 'Ni2', 'O', 'O', 'O', 'O']

.. code:: python

  >>> newstruct, settings = run_symmetrise_3d_structure(structure_afm, settings_dict)
  >>> settings.num_symops
  32
  >>> settings.space_group
  123

Since CRYSTAL17 expects the geometry in a standardized form,
which minimises the translational symmetry components,
he structure can be converted to a standardized,
and (optionally) primitive cell:

.. code:: python

  >>> settings_dict = {'primitive': True, 'standardize': True, 'idealize': False,
  ... 'kinds': {'fixed': [], 'ghosts': [], 'spin_alpha': [], 'spin_beta': []},
  ... 'angletol': None, 'symprec': 0.01}

  >>> newstruct, settings = run_symmetrise_3d_structure(structure, settings_dict)
  >>> newstruct.get_formula()
  'NiO'
  >>> settings.data.centring_code
  5

.. code:: python

  >>> newstruct, settings = run_symmetrise_3d_structure(structure_afm, settings_dict)
  >>> newstruct.get_formula()
  'Ni2O2'
  >>> settings.data.centring_code
  1

The other option is to ``idealize`` the structure, which
removes distortions of the unit cell's atomic positions,
compared to the ideal symmetry.

.. _main_calc_python_basis:

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
  >>> from aiida_crystal17.tests import TEST_DIR
  >>> fpath = os.path.join(TEST_DIR, "input_files", "sto3g", "sto3g_Mg.basis")

  >>> from aiida.plugins import DataFactory
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
          os.path.join(TEST_DIR, "input_files", "sto3g"),
          "sto3g", "group of sto3g basis sets",
          extension=".basis")

Basis families can be searched (optionally by the elements they contain):

.. code:: python

  >>> from aiida.plugins import DataFactory
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

  >>> from aiida.plugins import DataFactory
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


Input Preparation and Validation
--------------------------------

Before creating and submitting the calculation,
:py:class:`~.CryMainCalculation` provides a helper function,
to prepare the parameter and settings data
and validate their content.

.. code:: python

  from aiida.plugins import DataFactory, CalculationFactory
  StructureData = DataFactory('structure')
  calc_cls = CalculationFactory('crystal17.main')

  atoms = crystal(
      symbols=[28, 8],
      basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
      spacegroup=225,
      cellpar=[4.164, 4.164, 4.164, 90, 90, 90])
  atoms.set_tags([1, 1, 2, 2, 0, 0, 0, 0])
  instruct = StructureData(ase=atoms)
  settings_dict = {"kinds.spin_alpha": ["Ni1"],
                "kinds.spin_beta": ["Ni2"]}
  newstruct, settings = run_symmetrise_3d_structure(instruct, settings_dict)

  params = {
      "title": "NiO Bulk with AFM spin",
      "scf.single": "UHF",
      "scf.k_points": (8, 8),
      "scf.spinlock.SPINLOCK": (0, 15),
      "scf.numerical.FMIXING": 30,
      "scf.post_scf": ["PPAN"]
  }

  pdata = calc_cls.prepare_and_validate(params, newstruct,
                                        settings,
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
  calc = code.get_builder()

  calc.label = "aiida_crystal17 test"
  calc.description = "Test job submission with the aiida_crystal17 plugin"
  calc.set_max_wallclock_seconds(30)
  calc.set_withmpi(False)
  calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

  calc.use_parameters(pdata)
  calc.use_structure(newstruct)
  calc.use_settings(settings)
  calc.use_basisset_from_family("sto3g")

  calc.store_all()

  calc.submit()
