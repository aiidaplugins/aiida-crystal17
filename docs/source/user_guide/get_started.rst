===============
Getting started
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

To install from conda (recommended)::

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
