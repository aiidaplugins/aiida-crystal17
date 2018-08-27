[![Build Status](https://travis-ci.org/chrisjsewell/aiida-crystal17.svg?branch=master)](https://travis-ci.org/chrisjsewell/aiida-crystal17)

# aiida-crystal17

AiiDA plugin for running the [CRYSTAL17](http://www.crystal.unito.it/) code

## Installation

```shell
git clone https://github.com/chrisjsewell/aiida-crystal17 .
cd aiida-crystal17
pip install -e .  # also installs aiida, if missing (but not postgres)
#pip install -e .[pre-commit,testing] # install extras for more features
verdi quicksetup  # set up a new profile
verdi calculation plugins  # should now show the calclulation plugins (with prefix crystal17.)
```

## Usage

A quick demo of how to submit a calculation:

```shell
verdi daemon start         # make sure the daemon is running
cd examples
verdi run submit.py        # submit test calculation
verdi calculation list -a  # check status of calculation
```

## Tests

The following will discover and run all unit test:

```shell
pip install -e .[testing]
pytest -v
```

To omit tests which call `runcry17`:

```shell
pytest -v -m "not process_execution"
```

or alternatively to call the `mock_runcry17` executable, 
first set the global environmental variable:

```shell
export MOCK_EXECUTABLES=true
```

## Development and Testing Notes

The original plugin template was created from the 
[aiida-plugin-cutter
](https://github.com/aiidateam/aiida-plugin-cutter/tree/e614256377a4ac0c03f0ffca1dfe7bd9bb618983).

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

### Coding Style

The code style is tested using [prospector](https://prospector.readthedocs.io/en/master/),
with the configuration set in `.prospector.yaml`.

Editors like PyCharm have automatic code reformat utilities, which should adhere to this standard.

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
2. Additional output nodes (e.g. `StructureData` and `TrajectoryData`) 
and extending the data held in the `ParamaterData` node.
3. Parsing of input files to the input nodes described in (1), 
for migration of existing computations

## License

MIT

## Contact

chrisj_sewell@hotmail.com
