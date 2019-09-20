Properties Calculations
+++++++++++++++++++++++

.. todo:: Properties Calculation Workflow

.. note::

    More information to come...

The :py:class:`~.aiida_crystal17.workflows.crystal_props.base.CryPropertiesWorkChain` can be used to run properties
calculations from an existing :py:class:`~aiida_crystal17.calculations.cry_main.CryMainCalculation`.

.. code:: shell

    $ verdi plugin list aiida.workflows crystal17.properties
    Inputs
              cry:  required
             doss:  required
        wf_folder:  required  RemoteData  the folder containing the wavefunction fort.9 file
    clean_workdir:  optional  Bool        If `True`, work directories of all called calculation will be cleaned ...
         metadata:  optional
         test_run:  optional  Bool        break off the workchain before submitting a calculation
    Outputs
            doss:  required
    Exit codes
                1:  The process has failed with an unspecified error.
                2:  The process failed with legacy failure mode.
                10:  The process returned an invalid output.
                11:  The process did not register a required output.
                200:  Workchain ended before submitting calculation
                201:  The wf_folder does not contain a wavefunction file, and was not created by a crymaincalculation.
                202:  The crymaincalculation that created the wf_folder failed.
                203:  The crymaincalculation that created the wf_folder can not be used to restart a calculation.
                204:  The scf calculation failed.
                205:  The doss calculation failed
