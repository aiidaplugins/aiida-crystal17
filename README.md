[![Build Status](https://travis-ci.org/chrisjsewell/aiida-crystal17.svg?branch=master)](https://travis-ci.org/chrisjsewell/aiida-crystal17)
[![Coverage Status](https://coveralls.io/repos/github/chrisjsewell/aiida-crystal17/badge.svg?branch=master)](https://coveralls.io/github/chrisjsewell/aiida-crystal17?branch=master)
[![Docs status](https://readthedocs.org/projects/aiida-crystal17/badge)](http://aiida-crystal17.readthedocs.io/) 
[![PyPI](https://img.shields.io/pypi/v/aiida-crystal17.svg)](https://pypi.python.org/pypi/aiida-crystal17/)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/aiida-crystal17/badges/version.svg)](https://anaconda.org/conda-forge/aiida-crystal17)

# aiida-crystal17

AiiDA plugin for running the [CRYSTAL17](http://www.crystal.unito.it/) code. 
The code is principally tested against CRYSTAL17, 
but the output parsing has also been tested against CRYSTAL14.

**Documentation**: https://readthedocs.org/projects/aiida-crystal17

## Installation

To install from pypi:

```shell
>> pip install aiida-crystal17
```

To install the development version:

```shell
>> git clone https://github.com/chrisjsewell/aiida-crystal17 .
>> cd aiida-crystal17
>> pip install -e .  # also installs aiida, if missing (but not postgres)
>> #pip install -e .[pre-commit,testing] # install extras for more features
>> verdi quicksetup  # set up a new profile
>> verdi calculation plugins  # should now show the calclulation plugins (with prefix crystal17.)
```

## Usage

### Basic Calculation

The `crystal17.basic` is the simplest calculation plugin. 
It takes a pre-written .d12 file as input 
and (optionally) a .gui file with geometry, for .d12 inputs containing the `EXTERNAL` keyword.
Assuming AiiDA is configured and your database is running:

```shell
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
```

Once the calculation has run, it will be linked to the input nodes and a number of output nodes:

```shell
>> verdi calculation show 5
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
output_settings    9     StructSettingsData
output_structure   10    StructureData
##### LOGS:
There are 1 log messages for this calculation
Run 'verdi calculation logshow 5' to see them
```

The outputs represent:

-  ``remote_folder`` provides a symbolic link to the work directory
   where the computation was run.
-  ``retrieved`` stores a folder containing the full main output of
   ``runcry17`` (as main.out)
-  ``output_parameters`` stores a dictionary of key parameters in the
   database, for later querying.
-  ``output_structure`` stores the final geometry from the calculation
-  ``output_settings`` stores additional information on the structure,
    such as the symmetry operations.

For compatibility, parameters are named with the same convention as
``aiida-quantumespresso``:

.. code:: shell

    >> verdi data parameter show 8
    {
      "calculation_spin": false, 
      "calculation_type": "restricted closed shell", 
      "ejplugins_version": "0.9.7", 
      "energy": -7380.22160519032, 
      "energy_units": "eV", 
      "errors": [], 
      "mulliken_charges": [
        0.776999999999999, 
        -0.776999999999999
      ], 
      "mulliken_electrons": [
        11.223, 
        8.777
      ], 
      "number_of_assymetric": 2, 
      "number_of_atoms": 2, 
      "parser_class": "CryBasicParser", 
      "parser_version": "0.3.0a0", 
      "parser_warnings": [
        "no initial structure available, creating new kinds for atoms"
      ], 
      "scf_iterations": 7, 
      "volume": 18.65461525, 
      "wall_time_seconds": 5, 
      "warnings": []
    }

You can view the structure settings content by
(use ``-c`` to view the symmetry operations):

```shell
>> verdi data cry17-settings show 9
centring_code: 1
crystal_type:  1
num_symops:    48
space_group:   1
```

The final structure can be directly viewed by a number of different
programs (assuming the executables are available):

```shell
>> verdi data structure show --format xcrysden 10
```

### Main Calculation

The ``crystal17.main`` plugin is designed with a more programmatic
input interface. It creates the input ``.d12`` and ``.gui`` files,
from a set of AiiDa nodes.

```shell
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
```

Once the calculation has run, it will be linked to the input nodes and a
number of output nodes:

```shell
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
```

The inputs represent:

-  `parameters` is a dictionary of (structure independent) data,
    used to create the main.d12 file.
-  `structure` stores the initial atomic configuration for the calculation.
-  `settings` stores additional data related to the initial atomic
    configuration, such as symmetry operations and initial spin.
-  `basis_` store the basis set for each element.


## Tests

The following will discover and run all unit test:

```shell
>> pip install -e .[testing]
>> reentry scan -r aiida
>> pytest -v
```

To omit tests which call `runcry17`:

```shell
>> pytest -v -m "not process_execution"
```

or alternatively to call the `mock_runcry17` executable, 
first set the global environmental variable:

```shell
>> export MOCK_EXECUTABLES=true
```

## Development and Testing Notes

The original plugin template was created from the 
[aiida-plugin-cutter
](https://github.com/aiidateam/aiida-plugin-cutter/tree/e614256377a4ac0c03f0ffca1dfe7bd9bb618983).

### Coding Style Requirements

The code style is tested using [prospector](https://prospector.readthedocs.io/en/master/),
with the configuration set in `.prospector.yaml`, and [yapf](https://github.com/google/yapf).

Installing with `aiida-crystal17[pre-commit]` makes the [pre-commit](https://pre-commit.com/)
package available, which will ensure these tests are passed by reformatting the code 
and testing for lint errors before submitting a commit.
It can be setup by:

```shell
>> cd aiida-crystal17
>> pre-commit install
```

Optionally you can run `yapf` and `prospector` separately:

```shell
>> yapf -r -i .  # recusivel find and format files in-place
>> prospector 
```

Editors like PyCharm also have automatic code reformat utilities, which should adhere to this standard.

### Testing against mock CRYSTAL17 executables

Because CRYSTAL17 is a licensed software, it is not possible to source a copy of the executable on Travis CI.
Therefore, a mock executable (`mock_runcry17`) has been created for testing purposes (which also speeds up test runs). 

This executable computes the md5 hash of the supplied input file and tries to match it against a dictionary of 
precomputed hashes. If found, the executable will write the matching output (from `test/output_files`) to stdout.

To use this mock executable when running tests, set the global variable `MOCK_EXECUTABLES=true`.

### Setting up CRYSTAL17 locally

To set up local version of CRYSTAL17 on a mac (after downloading a copy from the distributor), I had to:

1. Remove the quarantine from the executable permissions:

    ```shell
    xattr -c crystal 
    xattr -c properties
    ```
    
2. Create versions of the lapack/blas libraries in the expected folders:

    ```shell
    sudo port install lapack
    sudo cp /opt/local/lib/lapack/liblapack.3.dylib /usr/local/opt/lapack/lib/liblapack.3.dylib
    sudo cp /opt/local/lib/lapack/libblas.3.dylib /usr/local/opt/lapack/lib/libblas.3.dylib
    ```
    
3. Define environmental variables in `~/.bashrc`, as detailed in `cry17_scripts/cry17.bashrc`
4. Copy or symlink the `cry17_scripts/runcry17` script into `/usr/local/bin/`

## License

MIT

## Contact

chrisj_sewell@hotmail.com
