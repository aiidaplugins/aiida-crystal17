.. _main_calculation_plugin:

========================
Main Calculation Plugin
========================

The ``crystal17.main`` plugin is designed with a more programmatic
input interface. It creates the input ``.d12`` and ``.gui`` files,
from a set of AiiDa
:py:class:`~aiida.orm.nodes.data.Data` nodes.

.. note::

  The approach mirrors closely that of the ``aiida-quantumespresso.pw`` plugin,
  which is discussed in :ref:`this tutorial <my-ref-to-pw-tutorial>`

.. note::

  See :ref:`main_calculation_immigrant` for a method
  to immigrate existing output/input files as a
  ``crystal17.main`` calculation.

This chapter will show how to launch a single CRYSTAL17 calculation.
We will look at how to run a computation *via* the terminal,
then how to construct the inputs for a computation in Python.
It is assumed that you have already performed the installation,
and that you already set up a computer (with verdi),installed CRYSTAL17
and the ``runcry17`` executable on the cluster and in AiiDA.
Although the code should be quite readable,
a basic knowledge of Python and object programming is useful.

.. toctree::
    :maxdepth: 3

    calc_main_cmndline
    calc_main_python
