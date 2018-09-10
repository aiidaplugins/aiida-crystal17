.. _main_calculation_immigrant:

============================
Main Calculation Immigration
============================

In order to immigrate existing CRYSTAL17 calculations,
the :py:func:`~.create_inputs` function has been written
to take a ``.d12`` and ``.out`` file set
and create the inputs required for ``crystal17.main``:

.. code:: python

    >>> import aiida_crystal17.tests as tests
    >>> from aiida_crystal17.parsers.migrate import create_inputs

import aiida_crystal17.tests.utils    >>> inpath = os.path.join(tests.TEST_DIR, "input_files",
    ...                       'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join(tests.TEST_DIR, "output_files",
    ...                        'nio_sto3g_afm.crystal.out')

    >>> inputs = create_inputs(inpath, outpath)

    >>> print(inputs)
    {'basis':
       {'Ni': <BasisSetData: uuid: f5edf8a7-23ca-4383-8aca-07cf22fdfbc4 (unstored)>,
        'O': <BasisSetData: uuid: 95859f1b-3822-4b60-92b2-238ec5a1931c (unstored)>},
     'parameters': <ParameterData: uuid: 16d9deb4-150a-455f-9055-cca6b1e0d93d (unstored)>,
     'structure': <StructureData: uuid: efaff664-41cc-4339-98d7-ea7594dfce52 (unstored)>,
     'settings': <ParameterData: uuid: 0ef11c68-32a5-4f5b-a783-d2e24da74328 (unstored)>}

This function is used by the :py

    >>> import aiida_crystal17.tests as tests
    >>> from aiida_crystal17.parsers.migrate import create_inputs

import aiida_crystal17.tests.utils    >>> inpath = os.path.join(tests.TEST_DIR, "input_files",
    ...                       'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join(tests.TEST_DIR, "output_files",
    ...                        'nio_sto3g_afm.crystal.out')

    >>> inputs = create_inputs(inpath, outpath)

    >>> print(inputs)
    {'basis':
       {'Ni': <BasisSetData: uuid: f5edf8a7-23ca-4383-8aca-07cf22fdfbc4 (unstored)>,
        'O': <BasisSetData: uuid: 95859f1b-3822-4b60-92b2-238ec5a1931c (unstored)>},
     'parameters': <ParameterData: uuid: 16d9deb4-150a-455f-9055-cca6b1e0d93d (unstored)>,
     'structure': <StructureData: uuid: efaff664-41cc-4339-98d7-ea7594dfce52 (unstored)>,
     'settings': <ParameterData: uuid: 0ef11c68-32a5-4f5b-a783-d2e24da74328 (unstored)>}

This function is used by the :py

    >>> import aiida_crystal17.tests as tests
    >>> from aiida_crystal17.parsers.migrate import create_inputs

import aiida_crystal17.tests.utils    >>> inpath = os.path.join(tests.TEST_DIR, "input_files",
    ...                       'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join(tests.TEST_DIR, "output_files",
    ...                        'nio_sto3g_afm.crystal.out')

    >>> inputs = create_inputs(inpath, outpath)

    >>> print(inputs)
    {'basis':
       {'Ni': <BasisSetData: uuid: f5edf8a7-23ca-4383-8aca-07cf22fdfbc4 (unstored)>,
        'O': <BasisSetData: uuid: 95859f1b-3822-4b60-92b2-238ec5a1931c (unstored)>},
     'parameters': <ParameterData: uuid: 16d9deb4-150a-455f-9055-cca6b1e0d93d (unstored)>,
     'structure': <StructureData: uuid: efaff664-41cc-4339-98d7-ea7594dfce52 (unstored)>,
     'settings': <ParameterData: uuid: 0ef11c68-32a5-4f5b-a783-d2e24da74328 (unstored)>}

This function is used by the :py

    >>> import aiida_crystal17.tests as tests
    >>> from aiida_crystal17.parsers.migrate import create_inputs

import aiida_crystal17.tests.utils    >>> inpath = os.path.join(tests.TEST_DIR, "input_files",
    ...                       'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join(tests.TEST_DIR, "output_files",
    ...                        'nio_sto3g_afm.crystal.out')

    >>> inputs = create_inputs(inpath, outpath)

    >>> print(inputs)
    {'basis':
       {'Ni': <BasisSetData: uuid: f5edf8a7-23ca-4383-8aca-07cf22fdfbc4 (unstored)>,
        'O': <BasisSetData: uuid: 95859f1b-3822-4b60-92b2-238ec5a1931c (unstored)>},
     'parameters': <ParameterData: uuid: 16d9deb4-150a-455f-9055-cca6b1e0d93d (unstored)>,
     'structure': <StructureData: uuid: efaff664-41cc-4339-98d7-ea7594dfce52 (unstored)>,
     'settings': <ParameterData: uuid: 0ef11c68-32a5-4f5b-a783-d2e24da74328 (unstored)>}

This function is used by the :py

    >>> import aiida_crystal17.tests as tests
    >>> from aiida_crystal17.parsers.migrate import create_inputs

import aiida_crystal17.tests.utils    >>> inpath = os.path.join(aiida_crystal17.tests.utils.TEST_DIR, "input_files",
    ...                       'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join(tests.TEST_DIR, "output_files",
    ...                        'nio_sto3g_afm.crystal.out')

    >>> inputs = create_inputs(inpath, outpath)

    >>> print(inputs)
    {'basis':
       {'Ni': <BasisSetData: uuid: f5edf8a7-23ca-4383-8aca-07cf22fdfbc4 (unstored)>,
        'O': <BasisSetData: uuid: 95859f1b-3822-4b60-92b2-238ec5a1931c (unstored)>},
     'parameters': <ParameterData: uuid: 16d9deb4-150a-455f-9055-cca6b1e0d93d (unstored)>,
     'structure': <StructureData: uuid: efaff664-41cc-4339-98d7-ea7594dfce52 (unstored)>,
     'settings': <ParameterData: uuid: 0ef11c68-32a5-4f5b-a783-d2e24da74328 (unstored)>}

This function is used by the :py

    >>> import aiida_crystal17.tests as tests
    >>> from aiida_crystal17.parsers.migrate import create_inputs

import aiida_crystal17.tests.utils    >>> inpath = os.path.join(aiida_crystal17.tests.utils.TEST_DIR, "input_files",
    ...                       'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join(tests.TEST_DIR, "output_files",
    ...                        'nio_sto3g_afm.crystal.out')

    >>> inputs = create_inputs(inpath, outpath)

    >>> print(inputs)
    {'basis':
       {'Ni': <BasisSetData: uuid: f5edf8a7-23ca-4383-8aca-07cf22fdfbc4 (unstored)>,
        'O': <BasisSetData: uuid: 95859f1b-3822-4b60-92b2-238ec5a1931c (unstored)>},
     'parameters': <ParameterData: uuid: 16d9deb4-150a-455f-9055-cca6b1e0d93d (unstored)>,
     'structure': <StructureData: uuid: efaff664-41cc-4339-98d7-ea7594dfce52 (unstored)>,
     'settings': <ParameterData: uuid: 0ef11c68-32a5-4f5b-a783-d2e24da74328 (unstored)>}

This function is used by the :py

    >>> import aiida_crystal17.tests as tests
    >>> from aiida_crystal17.parsers.migrate import create_inputs

import aiida_crystal17.tests.utils    >>> inpath = os.path.join(tests.TEST_DIR, "input_files",
    ...                       'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join(tests.TEST_DIR, "output_files",
    ...                        'nio_sto3g_afm.crystal.out')

    >>> inputs = create_inputs(inpath, outpath)

    >>> print(inputs)
    {'basis':
       {'Ni': <BasisSetData: uuid: f5edf8a7-23ca-4383-8aca-07cf22fdfbc4 (unstored)>,
        'O': <BasisSetData: uuid: 95859f1b-3822-4b60-92b2-238ec5a1931c (unstored)>},
     'parameters': <ParameterData: uuid: 16d9deb4-150a-455f-9055-cca6b1e0d93d (unstored)>,
     'structure': <StructureData: uuid: efaff664-41cc-4339-98d7-ea7594dfce52 (unstored)>,
     'settings': <ParameterData: uuid: 0ef11c68-32a5-4f5b-a783-d2e24da74328 (unstored)>}

This function is used by the :py

    >>> import aiida_crystal17.tests as tests
    >>> from aiida_crystal17.parsers.migrate import create_inputs

import aiida_crystal17.tests.utils    >>> inpath = os.path.join(tests.TEST_DIR, "input_files",
    ...                       'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join(tests.TEST_DIR, "output_files",
    ...                        'nio_sto3g_afm.crystal.out')

    >>> inputs = create_inputs(inpath, outpath)

    >>> print(inputs)
    {'basis':
       {'Ni': <BasisSetData: uuid: f5edf8a7-23ca-4383-8aca-07cf22fdfbc4 (unstored)>,
        'O': <BasisSetData: uuid: 95859f1b-3822-4b60-92b2-238ec5a1931c (unstored)>},
     'parameters': <ParameterData: uuid: 16d9deb4-150a-455f-9055-cca6b1e0d93d (unstored)>,
     'structure': <StructureData: uuid: efaff664-41cc-4339-98d7-ea7594dfce52 (unstored)>,
     'settings': <ParameterData: uuid: 0ef11c68-32a5-4f5b-a783-d2e24da74328 (unstored)>}

This function is used by the :py

    >>> import aiida_crystal17.tests as tests
    >>> from aiida_crystal17.parsers.migrate import create_inputs

import aiida_crystal17.tests.utils    >>> inpath = os.path.join(tests.TEST_DIR, "input_files",
    ...                       'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join(tests.TEST_DIR, "output_files",
    ...                        'nio_sto3g_afm.crystal.out')

    >>> inputs = create_inputs(inpath, outpath)

    >>> print(inputs)
    {'basis':
       {'Ni': <BasisSetData: uuid: f5edf8a7-23ca-4383-8aca-07cf22fdfbc4 (unstored)>,
        'O': <BasisSetData: uuid: 95859f1b-3822-4b60-92b2-238ec5a1931c (unstored)>},
     'parameters': <ParameterData: uuid: 16d9deb4-150a-455f-9055-cca6b1e0d93d (unstored)>,
     'structure': <StructureData: uuid: efaff664-41cc-4339-98d7-ea7594dfce52 (unstored)>,
     'settings': <ParameterData: uuid: 0ef11c68-32a5-4f5b-a783-d2e24da74328 (unstored)>}

This function is used by the :py

    >>> import aiida_crystal17.tests as tests
    >>> from aiida_crystal17.parsers.migrate import create_inputs

import aiida_crystal17.tests.utils    >>> inpath = os.path.join(tests.TEST_DIR, "input_files",
    ...                       'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join(tests.TEST_DIR, "output_files",
    ...                        'nio_sto3g_afm.crystal.out')

    >>> inputs = create_inputs(inpath, outpath)

    >>> print(inputs)
    {'basis':
       {'Ni': <BasisSetData: uuid: f5edf8a7-23ca-4383-8aca-07cf22fdfbc4 (unstored)>,
        'O': <BasisSetData: uuid: 95859f1b-3822-4b60-92b2-238ec5a1931c (unstored)>},
     'parameters': <ParameterData: uuid: 16d9deb4-150a-455f-9055-cca6b1e0d93d (unstored)>,
     'structure': <StructureData: uuid: efaff664-41cc-4339-98d7-ea7594dfce52 (unstored)>,
     'settings': <ParameterData: uuid: 0ef11c68-32a5-4f5b-a783-d2e24da74328 (unstored)>}

This function is used by the :py

    >>> import aiida_crystal17.tests as tests
    >>> from aiida_crystal17.parsers.migrate import create_inputs

import aiida_crystal17.tests.utils    >>> inpath = os.path.join(tests.TEST_DIR, "input_files",
    ...                       'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join(aiida_crystal17.tests.utils.TEST_DIR, "output_files",
    ...                        'nio_sto3g_afm.crystal.out')

    >>> inputs = create_inputs(inpath, outpath)

    >>> print(inputs)
    {'basis':
       {'Ni': <BasisSetData: uuid: f5edf8a7-23ca-4383-8aca-07cf22fdfbc4 (unstored)>,
        'O': <BasisSetData: uuid: 95859f1b-3822-4b60-92b2-238ec5a1931c (unstored)>},
     'parameters': <ParameterData: uuid: 16d9deb4-150a-455f-9055-cca6b1e0d93d (unstored)>,
     'structure': <StructureData: uuid: efaff664-41cc-4339-98d7-ea7594dfce52 (unstored)>,
     'settings': <ParameterData: uuid: 0ef11c68-32a5-4f5b-a783-d2e24da74328 (unstored)>}

This function is used by the :py

    >>> import aiida_crystal17.tests as tests
    >>> from aiida_crystal17.parsers.migrate import create_inputs

import aiida_crystal17.tests.utils    >>> inpath = os.path.join(tests.TEST_DIR, "input_files",
    ...                       'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join(aiida_crystal17.tests.utils.TEST_DIR, "output_files",
    ...                        'nio_sto3g_afm.crystal.out')

    >>> inputs = create_inputs(inpath, outpath)

    >>> print(inputs)
    {'basis':
       {'Ni': <BasisSetData: uuid: f5edf8a7-23ca-4383-8aca-07cf22fdfbc4 (unstored)>,
        'O': <BasisSetData: uuid: 95859f1b-3822-4b60-92b2-238ec5a1931c (unstored)>},
     'parameters': <ParameterData: uuid: 16d9deb4-150a-455f-9055-cca6b1e0d93d (unstored)>,
     'structure': <StructureData: uuid: efaff664-41cc-4339-98d7-ea7594dfce52 (unstored)>,
     'settings': <ParameterData: uuid: 0ef11c68-32a5-4f5b-a783-d2e24da74328 (unstored)>}

This function is used by the :py

    >>> import aiida_crystal17.tests as tests
    >>> from aiida_crystal17.parsers.migrate import create_inputs

    >>> inpath = os.path.join(tests.TEST_DIR, "input_files",
    ...                       'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join(tests.TEST_DIR, "output_files",
    ...                        'nio_sto3g_afm.crystal.out')

    >>> inputs = create_inputs(inpath, outpath)

    >>> print(inputs)
    {'basis': 
       {'Ni': <BasisSetData: uuid: f5edf8a7-23ca-4383-8aca-07cf22fdfbc4 (unstored)>,
        'O': <BasisSetData: uuid: 95859f1b-3822-4b60-92b2-238ec5a1931c (unstored)>},
     'parameters': <ParameterData: uuid: 16d9deb4-150a-455f-9055-cca6b1e0d93d (unstored)>,
     'structure': <StructureData: uuid: efaff664-41cc-4339-98d7-ea7594dfce52 (unstored)>,
     'settings': <ParameterData: uuid: 0ef11c68-32a5-4f5b-a783-d2e24da74328 (unstored)>}

This function is used by the :py:func:`~.migrate_as_main` function,
to create a full imitation of a ``crystal17.main`` calculation:

.. code:: python

    >>> from aiida import load_dbenv
    >>> load_dbenv()
    >>> from aiida_crystal17.workflows.cry_main_immigrant import migrate_as_main
    >>> work_dir = tests.TEST_DIR
    >>> inpath = os.path.join("input_files", 'nio_sto3g_afm.crystal.d12')
    >>> outpath = os.path.join("output_files", 'nio_sto3g_afm.crystal.out')
    >>> node = migrate_as_main(work_dir, inpath, outpath)
    >>> print(node.pk)
    2474

In the terminal this then looks like:

::

    >>> verdi calculation show 2474
    -----------  ----------------------------------------------------------------------------------------------------------------------
    type         WorkCalculation
    pk           2474
    uuid         b1812e1a-2576-4c70-8376-595dcde324b2
    label        CryMainImmigrant
    description  an immigrated CRYSTAL17 calculation into the <class 'aiida_crystal17.calculations.cry_main.CryMainCalculation'> format
    ctime        2018-09-09 00:51:27.256031+00:00
    mtime        2018-09-09 00:51:28.485742+00:00
    -----------  ----------------------------------------------------------------------------------------------------------------------
    ##### INPUTS:
    Link label      PK  Type
    ------------  ----  -------------
    basis_Ni      2456  BasisSetData
    basis_O       2453  BasisSetData
    parameters    2471  ParameterData
    structure     2472  StructureData
    settings      2473  ParameterData
    ##### OUTPUTS:
    Link label           PK  Type
    -----------------  ----  -------------
    output_arrays      2475  ArrayData
    output_parameters  2476  ParameterData
    output_structure   2477  StructureData
    retrieved          2478  FolderData

.. note::

    There is also a ``crystal17.immigrant`` calculation plugin,
    which works the same as :ref:`pwimmigrant-tutorial`.
    However, since this approach no longer works in
    ``aiida>=1.0``, it will be subject to change
    (see `this ongoing issue <https://github.com/aiidateam/aiida_core/issues/1892>`_).

