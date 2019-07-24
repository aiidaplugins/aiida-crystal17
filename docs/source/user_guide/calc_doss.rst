DOSS Calculation
++++++++++++++++

.. todo:: DOSS Calculation

.. note::

    More information to come...

The :py:class:`~.aiida_crystal17.calculations.cry_doss.CryDossCalculation` can be used to run the `properties`
executable for DOSS calculations, from an existing ``fort.9``.

.. code:: shell

    $ verdi plugin list aiida.calculations crystal17.doss
    Inputs
               code:  required  Code           The Code to use for this job.
         parameters:  required  Dict           the input parameters to create the DOSS input file.
          wf_folder:  required  RemoteData     the folder containing the wavefunction fort.9 file
           metadata:  optional
    Outputs
      remote_folder:  required  RemoteData     Input files necessary to run the process will be stored in this folder node ...
            results:  required  Dict           summary of the parsed data
          retrieved:  required  FolderData     Files that are retrieved by the daemon will be stored in this node. By defa ...
             arrays:  optional  ArrayData      energies and DoS arrays
          structure:  optional  StructureData  the structure output from the calculation
           symmetry:  optional  SymmetryData   the symmetry data from the calculation
    Exit codes
                  1:  The process has failed with an unspecified error.
                  2:  The process failed with legacy failure mode.
                 10:  The process returned an invalid output.
                 11:  The process did not register a required output.
                200:  The retrieved folder data node could not be accessed.
                210:  The main (stdout) output file was not found
                211:  The temporary retrieved folder was not found
                300:  An error was flagged trying to parse the crystal exec stdout file
                301:  An error occurred parsing the 'opta'/'optc' geomerty files
                302:  The crystal exec stdout file denoted that the run was a testgeom
                350:  The input file could not be read by crystal
                351:  Crystal could not find the required wavefunction file
                352:  Parser could not find the output isovalue (fort.25) file
                400:  The calculation stopped prematurely because it ran out of walltime.
                401:  The calculation stopped prematurely because it ran out of memory.
                402:  The calculation stopped prematurely because it ran out of virtual memory.
                411:  Scf convergence did not finalise (usually due to reaching step limit)
                412:  Geometry convergence did not finalise (usually due to reaching step limit)
                413:  An error encountered usually during geometry optimisation
                414:  An error was encountered during an scf computation
                415:  An unknown error was encountered, causing the mpi to abort
                499:  The main crystal output file flagged an unhandled error
                510:  Inconsistency in the input and output symmetry
                520:  Primitive symmops were not found in the output file


The :ref:`doss_input_schema` gives the allowed format of the input dictionary, for example::

    from aiida.orm import Dict
    Dict(dict={
        "shrink_is": 18,
        "shrink_isp": 36,
        "npoints": 100,
        "band_minimum": -10,
        "band_maximum": 10,
        "band_units": "eV"
    })
