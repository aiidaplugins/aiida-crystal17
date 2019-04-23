===============
Getting Started
===============

We show below a number of tutorials for the main CRYSTAL17 code
that will guide you through submitting your calculations using AiiDA.

Note: these tutorials assume you already installed AiiDA and
properly configured AiiDA and configured one CRYSTAL17 code.
You can check the
`main AiiDA-core documentation <http://aiida-core.readthedocs.io/en/latest/index.html>`_
for more information on how to perform these steps.

Installation
++++++++++++

|PyPI| |Conda|

To install from Conda (recommended)::

    >> conda install -c conda-forge aiida-crystal17
    >> conda install -c bioconda chainmap==1.0.2

To install from pypi::

    >> pip install aiida-crystal17

To install the development version::

    >> git clone https://github.com/chrisjsewell/aiida-crystal17 .
    >> cd aiida-crystal17
    >> pip install -e .  # also installs aiida, if missing (but not postgres)
    #>> pip install -e .[pre-commit,testing] # install extras for more features
    >> verdi quicksetup  # better to set up a new profile
    >> verdi calculation plugins  # should now show your calclulation plugins

Then use ``verdi code setup`` with a ``crystal17.`` input plugin
to set up an AiiDA code for that plugin.

CRYSTAL17 Executable
++++++++++++++++++++

``aiida-crystal17`` is designed to call the ``runcry17`` executable,
as supplied by CRYSTAL, and also can be found within the
`aiida-crystal17 repository <https://github.com/chrisjsewell/aiida-crystal17/tree/master/cry17_scripts>`_.
This is required to be available on the computer
that the calculations are being run on.

For test purposes, a ``mock_runcry17`` executable is installed with
``aiida-crystal17``, that will return pre-computed output files,
if parsed specific test input files. When running the test suite,
this executable will be used in place of ``runcry17``,
if the global variable ``export MOCK_CRY17_EXECUTABLES=true`` is set.

.. |PyPI| image:: https://img.shields.io/pypi/v/aiida-crystal17.svg
   :target: https://pypi.python.org/pypi/aiida-crystal17/
.. |Conda| image:: https://anaconda.org/conda-forge/aiida-crystal17/badges/version.svg
   :target: https://anaconda.org/conda-forge/aiida-crystal17