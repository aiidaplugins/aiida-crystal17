[![Build Status](https://travis-ci.org/chrisjsewell/aiida-crystal17.svg?branch=master)](https://travis-ci.org/chrisjsewell/aiida-crystal17)
[![Coverage Status](https://coveralls.io/repos/github/chrisjsewell/aiida-crystal17/badge.svg?branch=master)](https://coveralls.io/github/chrisjsewell/aiida-crystal17?branch=master)
[![Docs status](https://readthedocs.org/projects/aiida-crystal17/badge)](http://aiida-crystal17.readthedocs.io/) 

# aiida-crystal17

AiiDA plugin for running the [CRYSTAL17](http://www.crystal.unito.it/) code. 
The code is principally tested against CRYSTAL17, 
but the output parsing has also been tested against CRYSTAL14.

## Installation

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
>> verdi calculation show 2267
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

```

The outputs represent:

- `remote_folder` provides a symbolic link to the work directory where the computation was run.
- `retrieved` stores a folder containing the full stdout of `runcry17` (as main.out)
- `output_parameters` stores a dictionary of key parameters in the database, for later querying.
- `output_arrays` stores keys in the database to array data stored on file 
(such as symmetry operations and mulliken charges).
- `output_structure` stores the final geometry from the calculation

For compatibility, parameters are named with the same convention as `aiida-quantumespresso`:

```shell
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
```

The final structure can be directly viewed by a number of different programs (assuming the executables are available):

```shell
>> verdi data structure show --format xcrysden 10
```

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

### Current Development Status

#### Basic Crystal Calculation

This plugin set is the first to be developed. 
It provides a basic calculation functionality by:
 
1. Accepting a (pre-written) input file *via* a `SinglefileData` node
2. Initiating a crystal run *via* the `crystal17.basic` calculation plugin.
3. Parsing the stdout file into:

   1. an output a `SinglefileData` node
   2. an output `ParameterData` node, holding key data, *via* the `crystal17.basic` parser plugin.

### Future Development

Future development will then focus on:
 
1. Creation of the input file,  *via* input of 
    1. a `StructureData` node
    2. a main `ParamaterData` node.
    3. `ParamaterData` nodes for each atomic basis set
2. Additional output nodes (e.g. `TrajectoryData`) 
and extending the data held in the `ParamaterData` node.
3. Parsing of input files to the input nodes described in (1), 
for migration of existing computations

## License

MIT

## Contact

chrisj_sewell@hotmail.com
