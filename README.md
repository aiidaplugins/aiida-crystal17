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

To install from Conda (recommended)::

```shell
>> conda install -c conda-forge aiida-crystal17
>> conda install -c bioconda chainmap==1.0.2
```

To install from pypi::

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
>> yapf -r -i .  # recrusively find and format files in-place
>> prospector 
```

Editors like PyCharm also have automatic code reformat utilities, which should adhere to this standard.

### Testing against mock CRYSTAL17 executables

Because CRYSTAL17 is a licensed software, it is not possible to source a copy of the executable on Travis CI.
Therefore, a mock executable (`mock_runcry17`) has been created for testing purposes (which also speeds up test runs).

This executable computes the md5 hash of the supplied input file and tries to match it against a dictionary of
precomputed hashes. If found, the executable will write the matching output (from `test/output_files`) to stdout.

To use this mock executable when running tests, set the global variable `MOCK_CRY17_EXECUTABLES=true`.

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
