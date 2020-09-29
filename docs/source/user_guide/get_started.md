# Installation

[![PyPI](https://img.shields.io/pypi/v/aiida-crystal17.svg)](https://pypi.python.org/pypi/aiida-crystal17/) [![Conda](https://anaconda.org/conda-forge/aiida-crystal17/badges/version.svg)](https://anaconda.org/conda-forge/aiida-crystal17)

To install from pypi:

```shell
>> pip install --pre aiida-crystal17
```

To install from Conda:

```shell
>> conda install -c conda-forge aiida-crystal17 aiida-core.services
```

To install the development version:

```shell
>> git clone https://github.com/aiidaplugins/aiida-crystal17 .
>> cd aiida-crystal17
```

and either use the pre-written Conda development environment:

```shell
>> conda env create -n aiida_testenv -f conda_dev_env.yml python=3.6
>> conda activate aiida_testenv
>> pip install --no-deps -e .
```

or install all *via* pip:

```shell
>> pip install -e .
```

:::{note}
This will not install Postgres and RabbitMQ
:::

To configure aiida see the AiiDA Documentation: {ref}`aiida:intro:get_started`.

You should then see the crystal17 plugins in ``verdi``:

```shell
>> verdi calculation plugins
```

Then use ``verdi code setup`` with a ``crystal17.`` input plugin
to set up an AiiDA code for that plugin.

:::{seealso}
AiiDA documentation: {ref}`aiida:how-to:run-codes`
:::

# CRYSTAL17 Executable

``aiida-crystal17`` is designed to directly call the ``crystal`` or ``properties`` binary executables (or their parallel variants, e.g. ``Pcrystal``).
This is required to be available on the computer that the calculations are being run on.

If the code is called as a serial run (``metadata.options.withmpi=False``),
then the input file will be piped to the executable *via* stdout (as required by ``crystal``):

```bash
crystal < INPUT > main.out 2>&1
```

Whereas, if the code is called as a parallel run
(``metadata.options.withmpi=True``),
then the ``INPUT`` file is placed in the directory,
and the executable will read from it (as required by ``Pcrystal``):

```bash
mpiexec Pcrystal > main.out 2>&1
```

Note that, using the standard AiiDA schedulers,
the calculations will run directly in the working directory,
i.e. the files will not be copied to/from a temporary directory.
If this is required, then the ``prepend_text`` and ``append_text``
features of the ``Code`` node should be utilised.

:::{seealso}
AiiDA documentation: {ref}`aiida:how-to:run-codes`
:::

For test purposes, ``mock_crystal17`` and ``mock_properties17`` executables
are installed with ``aiida-crystal17``, that will return pre-computed output files,
if parsed specific test input files (based on the contents hash).
When running the test suite, these executable will be used in place of ``crystal``,
unless ``pytest --cry17-no-mock`` is used.

# Development

## Testing

Using tox is the best way to run the test-suite:

```shell
>> cd aiida-crystal17
>> tox -e py37
```

To omit tests which call external executables (like ``crystal17``):

```shell
>> tox -e py37 -- --cry17-skip-exec
```

To call the actual executables (e.g. ``crystal17`` instead of ``mock_crystal17``):

```shell
>> tox -e py37 -- --cry17-no-mock
```

To output the results of calcjob executions to a specific directory:

```shell
>> tox -e py37 -- --cry17-workdir "test_workdir"
```

## Coding Style Requirements

The code style is tested using [pre-commit](https://pre-commit.com),
which will ensure these tests are passed by reformatting the code and testing for lint errors before submitting a commit:

```shell
>> pip install pre-commit
>> pre-commit run --all
```

Optionally you can install this to run before all commits:

```shell
>> pre-commit install
```

## Documentation

The documentation can be created locally by running tox:

```shell
>> tox -e py37-docs-clean
>> tox -e py37-docs-update
```

Or directly:

```shell
>> cd aiida-crystal17/docs
>> make clean
>> make  # or make debug
```

:::{tip}
You can sync the notebooks in the `docs/source/notebooks/` folder, with Markdown representations (for easier editing), by running:

```shell
>> tox -e py37-sync
```

This will first generate the Markdown files,
edit them, then on re-running the sync, the notebooks will be updated.

Run `rm docs/source/notebooks/*.md` before docs builds.
:::
