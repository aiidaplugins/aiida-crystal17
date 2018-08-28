===============
Getting started
===============

This page should contain a short guide on what the plugin does and
a short example on how to use the plugin.

Installation
++++++++++++

Use the following commands to install the plugin::

    git clone https://github.com/chrisjsewell/aiida-crystal17 .
    cd aiida-crystal17
    pip install -e .  # also installs aiida, if missing (but not postgres)
    #pip install -e .[pre-commit,testing] # install extras for more features
    verdi quicksetup  # better to set up a new profile
    verdi calculation plugins  # should now show your calclulation plugins

Then use ``verdi code setup`` with the ``crystal17.basic`` input plugin
to set up an AiiDA code for crystal17.basic.

Usage
+++++

Basic Calculation
~~~~~~~~~~~~~~~~~

The ``crystal17.basic`` is the simplest calculation plugin. It takes a
pre-written .d12 file as input and (optionally) a .gui file with
geometry, for .d12 inputs containing the ``EXTERNAL`` keyword. Assuming
AiiDA is configured and your database is running:

.. code:: shell

   >> verdi daemon start         # make sure the daemon is running
   >> cd examples
   >> verdi run test_submit_basic.py       # submit test calculation
   submitted calculation; calc=Calculation(PK=5)
   >> verdi calculation list -a  # check status of calculation
     PK  Creation    State           Sched. state    Computer    Type
   ----  ----------  --------------  -------------  ----------  ---------------------------
   5     1m ago      WITHSCHEDULER                  localhost   crystal17.basic
   >> verdi calculation list -a  # after a few seconds
     PK  Creation    State           Sched. state    Computer    Type
   ----  ----------  --------------  -------------  ----------  ---------------------------
   5     1m ago      FINISHED        DONE           localhost   crystal17.basic

Once the calculation has run, it will be linked to the input nodes and a
number of output nodes:

.. code:: shell

   verdi calculation show 2267
   -----------  ---------------------------------------------------
   type         CryBasicCalculation
   pk           5
   uuid         3d9f804b-84db-443a-b6f8-69c15d96d244
   label        aiida_crystal17 test
   description  Test job submission with the aiida_crystal17 plugin
   ctime        2018-08-27 15:23:38.670705+00:00
   mtime        2018-08-27 15:24:26.516127+00:00
   computer     [2] localhost
   code         runcry17
   -----------  ---------------------------------------------------
   ##### INPUTS:
   Link label       PK    Type
   ---------------  ----  --------------
   input_external   3     SinglefileData
   input_file       4     SinglefileData
   ##### OUTPUTS:
   Link label           PK  Type
   -----------------  ----  -------------
   remote_folder      6     RemoteData
   retrieved          7     FolderData
   output_parameters  8     ParameterData
   output_arrays      9     ArrayData
   output_structure   10    StructureData
   ##### LOGS:
   There are 1 log messages for this calculation
   Run 'verdi calculation logshow 5' to see them

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

For compatibility, parameters are named with the same convention as
``aiida-quantumespresso``:

.. code:: shell

    >> verdi data parameter show 8
    {
      "calculation_spin": false,
      "calculation_type": "restricted closed shell",
      "ejplugins_version": "0.9.6",
      "energy": -7380.22160519032,
      "energy_units": "eV",
      "errors": [],
      "number_of_assymetric": 2,
      "number_of_atoms": 2,
      "number_of_symmops": 48,
      "parser_class": "CryBasicParser",
      "parser_version": "0.1.0a0",
      "parser_warnings": [],
      "scf_iterations": 7,
      "volume": 18.65461525,
      "wall_time_seconds": 4,
      "warnings": []
    }


The final structure can be directly viewed by a number of different
programs (assuming the executables are available):

.. code:: shell

   >> verdi data structure show --format xcrysden 10

