Installation
++++++++++++

|PyPI| |Conda|

To install from Conda (recommended)::

    >> conda install -c conda-forge aiida-crystal17 aiida-core.services

To install from pypi::

    >> pip install --pre aiida-crystal17

To install the development version::

    >> git clone https://github.com/chrisjsewell/aiida-crystal17 .
    >> cd aiida-crystal17

and either use the pre-written Conda development environment (recommended)::

    >> conda env create -n aiida_testenv -f conda_dev_env.yml python=3.6
    >> conda activate aiida_testenv
    >> pip install --no-deps -e .

or install all *via* pip::

    >> pip install -e .  # note this won't install postgres and rabbitmq
    #>> pip install -e .[code_style,testing,docs] # install extras for more features

To configure aiida::

    >> rabbitmq-server -detached >/dev/null 2>&1
    >> eval "$(_VERDI_COMPLETE=source verdi)"
    >> verdi quicksetup  # better to set up a new profile
    >> verdi status
    >> verdi calculation plugins  # should now show your calclulation plugins

Then use ``verdi code setup`` with a ``crystal17.`` input plugin
to set up an AiiDA code for that plugin.

.. seealso::

    The `AiiDA documentation <http://aiida-core.readthedocs.io>`_,
    for more general information on configuring and working with AiiDa.

CRYSTAL17 Executable
++++++++++++++++++++

``aiida-crystal17`` is designed to directly call
the ``crystal`` or ``properties`` binary executables
(or their parallel variants, e.g. ``Pcrystal``).
This is required to be available on the computer
that the calculations are being run on.

If the code is called as a serial run (``metadata.options.withmpi=False``),
then the input file will be piped to the executable *via* stdout
(as required by ``crystal``)::

    crystal < INPUT > main.out 2>&1

Whereas, if the code is called as a parallel run
(``metadata.options.withmpi=True``),
then the ``INPUT`` file is placed in the directory,
and the executable will read from it (as required by ``Pcrystal``)::

    mpiexec Pcrystal > main.out 2>&1

Note that, using the standard AiiDA schedulers,
the calculations will run directly in the working directory,
i.e. the files will not be copied to/from a temporary directory.
If this is required, then the ``prepend_text`` and ``append_text``
features of the ``Code`` node should be utilised.

.. seealso::

    AiiDA documentation: :ref:`aiida:setup_code`

For test purposes, ``mock_crystal17`` and ``mock_properties17`` executables
are installed with ``aiida-crystal17``,
that will return pre-computed output files,
if parsed specific test input files. When running the test suite,
this executable will be used in place of ``crystal``,
if the global variable ``export MOCK_CRY17_EXECUTABLES=true`` is set.

Development
+++++++++++

Testing
~~~~~~~

|Build Status| |Coverage Status|

The following will discover and run all unit test:

.. code:: shell

   >> cd aiida-crystal17
   >> pytest -v

To omit tests which call the ``crystal`` executable:

.. code:: shell

   >> pytest -v -m "not process_execution"

or alternatively to call the ``mock_crystal17`` executable, first set the
global environmental variable:

.. code:: shell

   >> export MOCK_CRY17_EXECUTABLES=true

Coding Style Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~

The code style is tested using `flake8 <http://flake8.pycqa.org>`__,
with the configuration set in ``.flake8``, and code should be formatted
with `yapf <https://github.com/google/yapf>`__ (configuration set in
``.style.yapf``).

Installing with ``aiida-crystal17[code_style]`` makes the
`pre-commit <https://pre-commit.com/>`__ package available, which will
ensure these tests are passed by reformatting the code and testing for
lint errors before submitting a commit. It can be setup by:

.. code:: shell

   >> cd aiida-crystal17
   >> pre-commit install

Optionally you can run ``yapf`` and ``flake8`` separately:

.. code:: shell

   >> yapf -i path/to/file  # format file in-place
   >> flake8

Editors like VS Code also have automatic code reformat utilities, which
can check and adhere to this standard.

Documentation
~~~~~~~~~~~~~

The documentation can be created locally by:

.. code:: shell

   >> cd aiida-crystal17/docs
   >> make clean
   >> make  # or make debug

.. |PyPI| image:: https://img.shields.io/pypi/v/aiida-crystal17.svg
   :target: https://pypi.python.org/pypi/aiida-crystal17/
.. |Conda| image:: https://anaconda.org/conda-forge/aiida-crystal17/badges/version.svg
   :target: https://anaconda.org/conda-forge/aiida-crystal17
.. |Build Status| image:: https://travis-ci.org/chrisjsewell/aiida-crystal17.svg?branch=master
   :target: https://travis-ci.org/chrisjsewell/aiida-crystal17
.. |Coverage Status| image:: https://coveralls.io/repos/github/chrisjsewell/aiida-crystal17/badge.svg?branch=master
   :target: https://coveralls.io/github/chrisjsewell/aiida-crystal17?branch=master
