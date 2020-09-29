# Changelog

## v0.10.0b5 (2019-10-18)

- Large improvement/refactor of properties calculations and workchains:

  - Rename ``cry_`` -> ``prop_``
  - Renamed ``crystal17.fermi`` -> ``crystal17.newk``
  - Subclass calculations from base ``PropAbstractCalculation``;
    - all calculation take as input a wf_folder and parameter dict
    - all calculations output a result dict
    - no longer options to symlink wf_folder (it doesn't work)
    - wf_folder can now be a standard folder (or remote)
  - Add raw parsers for parsing properties stdout and gaussian cube files.
  - Parsers all use ``read_properties_stdout`` to parse standard output data, and check for errors,
    also exit codes are saved for each step, then the highest priority code is returned at the end.
  - Changed inputs/outputs of ``crystal17.fermi``.
  - Add ``crystal17.ech3`` calculation and parser (stores cube files as ``GaussianCube`` data objects).
  - Updated CryPropertiesWorkChain to run multiple properties calculation.
  - Add creation of VESTA file, from cube data file.
  - ``crystal17.doss``; fix parsing of projections.
  - Update band_gap calcfunction, to use correct energy units format.
  - Add documentation: ``calc_doss``, ``workflow_properties``, ``calc_ech3``.

- Improve CRYSTAL main stdout parser.

  - Extract mulliken orbital and shell populations.
  - parse 0D (MOLECULE) cartesian coordinates
  - improve regex for removing PROCESS and Fortran warning lines
  - ignore ``all open_hca: getaddr_netdev ERROR`` lines, that can occur before program start.
  - fix issues with computations that converge after the 1st cycle.

- Add fort.9 raw parser.

- Symmetry: allow for use of symbol (rather than kind) to define
  inequivalent sites.

- Improved `BasisSetData.set_file` and `BasisSetData.upload_basisset_family`,
  to accept `pathlib.Path` and filelike objects.

- Problematically Access Resource Files:

  Non-python files (JSON schema and raw files) are now accessed programatically,
  using the `importlib_resources` package.
  This means that (a) they can be accessed even if the package is zipped and,
  (b) these files can be moved to a separate package in the future.

- Replace Travis flake8/version tests with a pre-commit test:

  - Updated `pre-commit` and `yapf` versions have been updated, and
  - `pre-commit run -a` has been applied to the repository.
  - Added conda test, to check the `conda_dev_env.yml` works.

- Add pytest plugin configuration:

  - Use pytest command-line arguments to control run configuration.
  - Replace ``MOCK_CRY17_EXECUTABLES`` environmental variable with
    ``pytest --cry17-no-mock``,
    and ``CRY17_TEST_WORKDIR`` with ``pytest --cry17-workdir "test_workdir"``.
  - Add ``--cry17-skip-exec``, for skipping tests call executable.
  - Add ``pytest-notebook`` dependency and test function, to test and regenerate tutorial notebooks.

- GULP: improve ReaxFF parser:

  - correctly handle read/write of ``X`` symbol
  - allow reaxff tolerance value to be set, when reading file to dict.

## v0.9.2b5 (2019-08-01)

- Add documentation.
- Add doss fort.25 parsing from cmndline.
- Add ``compute_orbitals`` function.
- Implement parse_bsets_stdin to create BasisSetData.
- Add licence to all python files and pre-commit format.
- Change copyright license.
- Add basis set parser and tests.
- Rename gui_parse to parse_fort34.
- Make check for num_operations==nsymops in 'gui_file_read' optional.

  This is not set for TESTGEOM output.
- Allow for 'trigonal' and 'rhombohedral' crystal types in gulp geometry
  input (these are subsets of 'hexagonal').


## v0.9.1b5 (2019-07-25)

- Remove ``version`` key from process attribute comparisons in tests.

- Add command line functions for parsing crystal stdout and stdin files
  (#16)
- Update Documentation.

  Restructure documentation into separate indexes and add guides for:

  - ``CryDossCalculation``
  - ``BaseRestartWorkChain``
  - ``CryPropertiesWorkChain``

  Also add ``doc8`` to ``pre-commit`` and fix ``conda_dev_env.yaml``
- ``BaseRestartWorkChain``: allow handlers to override exit status.

  Mirrors aiidateam/aiida-quantumespresso commit 35299616a03625fe899d63051f6a7c78dc53408e

  Sometimes a calculation returns a non-zero exit code indicating it is
  failed, but it can actually still be considered successful by the
  workchain. In this case, the handler wants to override the exit code of
  the calculation and return ``ExitCode(0)`` to indicate that the workchain
  is successful despite the last calculation being failed. To facilitate
  this the logic in the ``BaseRestartWorkChain`` is updated to detect zero
  being returned by a handler.

  In addition, to make this work, the default value of the ``exit_code`` for
  an ``ErrorHandlerReport`` tuple needs to be ``None`` to be able to
  distinguish when ``ExitCode(0)`` is purposefully returned.
- Improve getting started documentation.
- Add development instuctions for creating documentation.
- Fix heading levels.
- Improve install and development instructions.
- Add pip dev install of root package to conda usage instuctions.
- Add ``aiida-core.services`` to conda development environment.
- Upgrade ipypublish dependancy to 0.10.7.
- Update pre-commit configuration and upgrade RTD's to Sphinx v2 (#14)

- Add warning for fortran floating-point exceptions.
- Minor fixes (#13)

  - fix ``crystal17.doss`` test (when run with non-mock executable)
  - reformat crystal_stdout.py (with yapf line_length=120)
  - added additional tests for stdout parser (molecule and testgeom)
  - add description of how computation runs for serial and parallel modes
  - for ase requirements ase 3.18 is not compatible with python < 3.5.


## v0.9.0b5 (2019-07-18)

- Added documentation for ``crystal17.main.base`` workflow.
- Updated documentation and removed graph.py (now in aiida-core)
- Upgraded to aiida-core==1.0.0b5.
- Moved fort.25 parsing internally, and removed ejplugins dependancy.
- Use internal stdout parser for ``crystal17.main``

  This builds and improves on the original ejplugins implementation:
  making the parsing flow more easy to understand,
  adding additional data parsing (some taken from tilde),
  and restructuring the output json.
- Record the order of configuration names in the ``gulp.fitting`` results
  node.
- Output a new potential, resulting from the ``gulp.fitting``
- Hard code breaking terms in ``read_atom_section``
- Add line breaking (with ``&``) to reaxff potential lines longer than 78
  characters.
- Add reading of lennard potential files.
- Format lennard-jones number valuesin input file.
- Add band gap calcfunction.
- Add ``CryPropertiesWorkChain`` and tests.

  Also:

  - sort output of basis sets (by element) in crystal INPUT file
  - moved/re-computed doss/fermi raw test files
  - added environmental variable to run test computations in non-tempdir
  - doc string improvements.
- Fix reading gulp tables that have values replaced with
  \*\*\*\*\*\*\*s.

  Sometimes values can be output as \*'s (presumably if they are too large)
- Improve docstring of ``CryInputParams``
- Added functionality to run GULP calculations with 1-d structures.
- Add a settings input node to ``GulpFittingCalculation``
- Update package version in tests.
- Version bump.
- Add extra info to fitting parser.
- Rewrote GULP execution and parsing.

  - The input file is no streamed to ``gulp`` via stdin and outputs are captured from stdout and stderr.
  - Single/Opt raw parser rewrote, to be inline with fitting parser
  - Exit codes updated and added
  - stderr file read and added to 'warnings' key of results
  - added dump file to fitting output
  - made calculation have data_regression checks.
- Store names of files in potential repo (rather than using class
  attributes)
- Retrieve fitting flag info from potential creation, and store
  potential dict in repo (rather than as attributes)
- Added input creation for reaxff fitting.
- Added outout of fitting.
- Finalised creation of fitting input file (implemented for ``lj``)
- Add checks for index keys.
- Refactored reaxff keys and gulp write (in preparation for adding
  fitting flags)
- Create gulp_fitting_flags.yaml.
- Store full potential file in PotentialData (rather than creating on
  calculation submission)

  Then we don't have to rely on the external modules being there at calculation time.
  Also change potential keys from ``id1.id2`` to ``id1-id2`` (since AiiDa doesn't allow attributes with '.'s)
- Standardised GULP potentials.

  All potentials should share the a common jsonschema

  Also added reaxff tests, and initial implementation of fitting calculation.
- Restructure gulp raw test files.
- Run program directly from ``crystal`` executable, and add
  ``CryMainBaseWorkChain`` (#9)

  Before the calculations were running from ``runcry17``,
  which is a bash script that copies the files to/from a temporary folder,
  and changes the names of the files.
  This functionality should all be handled by other parts of the AiiDA machinery,
  so running from the base binary is more appropriate, and allows for more functionality.

  Additionally:

  - added restart functionality to ``CryMainCalculation`` (\*via\* a fort.9 in a remote folder)
  - added checks and error codes for PbsPro messages to ``_scheduler_stderr.txt`` (e.g. walltime limit reached)
  - allow SHRINK IS input to be a list ([IS1, IS2, IS3])
  - added output of ``TrajectoryData`` of optimisation steps for ``CryMainCalculation``
  - added ``CryMainBaseWorkChain`` (a replica of ``PwBaseWorkChain``  from ``aiida-quanumespresso``)
  - improved testing infrastructure
  - updated documentation.
- Fix ``KindData`` docstrings.
- Move test files to correct place.
- Combatibility test fixes.
- Added crystal.fermi calculation.
- Add crystal17.doss calculation.
- Change doss input format.
- Make num_regression test optional (on pandas ImportError)
- Added DOSS output (f25) raw parser.
- Add DOSS raw input parsers.
- Minor updates.
- Ensure cif to structure conversion provenance is stored.
- Update calc_main_immigrant.ipynb.
- Move tests to central folder.
- Rewrite immigration functions.
- Update aiida-core version to 1.0.0b4.
- Graph improvements.

  - add global_edge_style
  - color excepted processes red.
- Graph improvements.

  - Change ``include_calculation_intputs`` - > ``include_process_intputs``,
    and ``include_calculation_outputs`` - > ``include_process_outputs``
  - include link_pair in edge set, so that multiple (unique) links can exist between nodes
  - add sublabel for Str, Bool and UpfData.

- Allow additional keys in the dictionary (so it can be used for other
  purposes)
- Improve ``crystal17.sym3d``

  ``Symmetrise3DStructure`` now accepts a settings ``Dict`` containing the settings data.
  This is validated against a jsonschema.

  - kind names can also now be reset
  - add exit codes
  - add addational tests
  - update documentation.
- Add some helpful methods for manipulating StructureData.


## v0.6.0b3 (2019-06-22)

- Improve fractional <-> cartesian conversion.

  Use efficient numpy functions.
- Use kinds from input structure, in ``gulp.optimize`` parser.
- Fix  ``gulp.optimize`` parser, if the optimisation does not converge.

  - ensure the correct exit_code is returned
  - ensure the output cif is still read, and the output structure node created
  - add test.
- Improve crstal17.main error reporting, and add tests.

  Added lots more error codes, and the parser maps the error messages,
  extracted from the CRYSTAL output file, to the most appropriate one.
- Move raw file content parsers to a submodule.

  To make it more obvious what is the aiida Parser plugin.
- Move pytest timeout to configuration file.
- Update readme conda install.
- Update conda installation command.
- Don't retrieve input file (since it is already stored in CalcJob repo)
- Fix creation of output structure from cif.
- Add gulp potential class to entry points.
- Add EmpiricalPotential node type for gulp potential input.
- Use ase for cif converter.
- Update Symmetrise3DStructure workflow and add tests.
- Move structure creation in tests to pytest fixture.
- Add an exit code for non optimised calculations.
- Fix symmetry restricted computations for GULP.

  When including symmetry restrictions in GULP input files,
  only symmetry inequivalent sites (and) positions should be listed.
  We parse these in the symmetry input node.
- Retrieve input file for GULP computations.
- Add method for getting the spacegroup info of a symmetry node.
- Require correct symmetry input node type (crystal17.symmetry)
- Remove pypi deployment flag from python=2.7 tests.


## v0.5.0b3 (2019-06-13)

- Add GULP calculations (#4)

  - update aiida-core to v1.0.0b3
  - added GULP calculations, tests and documentation
  - add dependencies for reading CIF files
  - implement calculation submission tests (using process.prepare_for_submission)
  - implement new calculation immigration method
  - re-number calculation exit codes
  - update readthedocs build.
- Update .travis.yml.
- Update to aiida-core v1.0.0b2 (#2)

  Essentially rewrote the entire package.

## v0.4.1 (2019-03-03)

- Bug fix for pbc not 3.
- Added conda install info.
- Update test_parse_geometry.py.


## v0.4.0 (2019-03-02)

- Round coordinates.
- Change mock_runcry17 to an entry_point.
- Replace aiida_core atomic_tools extras with subset.
- Update geometry.py.
- Update test_cry_basic.py.
- Remove pymatgen dependency from tests.
- Update .travis.yml.
- Setup for conda dist.
- Updated computer get method for develop (1.0.0a2)

## v0.3.1a1 (2018-09-15)

- Omit tests from coverage report.
- Updated doc on installation.
- Updated readme and added pypi deployment.


## v0.3.0a1 (2018-09-12)

- Updated documentation.
- Potential fix for aiida v0.12 process runs.
- Added cmndline tests.
- Added cmnd line plugins.
- Don't output structure in no optimisation.
- Store fractional symops instead of cartesian.
- Convert output operations fractional coordinates to cartesian
  coordinates.
- Compare_operations improvement.
- Moved operation comparison to StructSettingsData.
- Replaced output_arrays with output_settings.
- Refactored structure manipulation as two-step process.
- Added full run test for main calc.
- Use input structure to get kinds.
- Added run_get_node util.
- Added StructSettingsData (and tests)
- Added skipif mark in pytest.
- Roll back commit.
- Possible fix for sqalchemy get_authinfo.
- Refactored test utils and added allowed fails.
- Remove ignored tests.
- Revert "test"

  This reverts commit ba2047e5465f0f826ca08a0cb6b5e3a552bba22c.
- Added development sqlalchemy test.
- Turn off caching.
- Added full execution test.
- Added immigrant documentation.
- Added input linking to immigrant creation.
- Added immigrant example.
- Added retrieved folder to outputs of immigrant.
- Added rabbitmq to services.
- Added pytest-tornado.
- Added pytest-timeout.
- Added migration workflow function.
- Api documentation update.
- Refactored parser to extract mainout parsing.
- Added immigrant as plugin.
- Add to test.
- Added CryMainImmigrant (and tests)
- Added computer configuration to computer configuration.
- Added migrate.create_inputs.
- Added basis set validation.
- Added read_inputd12 (and tests)
- Removed diff modules and updated version.

## v0.2.0a0 (2018-09-05)

- Finished initial crystal17.main documentation.
- Refactored geometry and added documentation.
- Added initial Settings documentation.
- Added full api to docs.
- Added test documentation.
- Minor doc update.
- Initial addition of main calculation documentation.
- End-to-end test fixes (relaying atomid_kind_map to parser)
- Added crystal.main example.
- Moved atom_props creation to own method and addto to
  prepare_and_validate.
- Added test with spin.
- Added atom specific properties to output d12.
- Move validation to separate module.
- Break symmetry by kind.
- Added kinds section to settings dict.
- Added BasisSetData input to .d12 creation.
- Refactored BasisSetData to store file content separately to metadata.
- Added python 3 compatabilty.
- Added BasisSetData plugin (and tests)
- Added settings schema.
- Added inputd12 writer.
- Added .gui creation and input schema.
- Added template implementation of crystal17.main calculation plugin.
- Remove stdoout since file isn't actually created via this.
- Coverage only for package.
- Add coverage setting and badge.
- Add testing requirement for coverage.
- Add test coverage reporting.
- Skip failing test for develop branch.
- Added initial .gui read/write and testing.
- Added symmops and arraydata output.
- Remove separate pip install.
- Updated readme on code style.
- Update pre-commit versions and ignored folders.
- Merged style and version into pre-commit.
- Changed diff to crystal17.diff and added correct requirement extra.
- Run yapf formatting.
- Added todo extension.
- Updated documentation.
- Added mulliken parsing.
- Improvements to tests.
- Remove computers workdir after testing.
- Enforce pytest 3.6.3 (for aiida develop)

  See https://github.com/aiidateam/aiida_core/issues/1911#issuecomment-416470291.
- Added user guide for ``crystal17.basic``
- Added example and documentation.
- Remove ase install.
- Added to readme.
- Updated some things in line with aiida-plugin-cutter.

  Upto commit on on Aug 27, 2018 873921e327a0944884088a11ae1548b00ccff7e7.
- Added optional input of external geometry file (and testing)
- Added initial parser and tests.
- Initial implementation and testing of crystal17.basic parser.
- Typo stopped extras installing.
- Added output file check.
- Test for files output by calculation.
- Fixed locating executable scripts created by pip install.
- Added tests for process execution.
- Added basic crystal parser.
- Test running diff calc.
- Style correction.
- Added mock CRYSTAL17 executable and refactored testing.
- Added basic crystal computation and sumbission test.
- Test correction.
- Corrected cry17_script location.
- Split version and style checks.
- Added local CRYSTAL17 setup scripts.
- Changed example entrance potins.
- Spilt session coped test fixture into overarching conftest.py.

  As per https://docs.pytest.org/en/latest/fixture.html#conftest-py-sharing-fixture-functions.
- Changes to pass pylint test.
- Revert "try adding pre-commit test (6)"

  This reverts commit 6e7a33d1ac4baa2f406f200e799484376d087f13.
- Revert "try without reentry scan"

  This reverts commit a12dc048c9168b4718c00ecc39865de70d125bc9.
- Refactored modules and updated test setup.
- Travis: ignore examples folder.
- Travis: load plugins.
- Change tests from unittest to pytest.
- Remove version check for travis.
- Changed to template from https://github.com/aiidateam/aiida-plugin-
  cutter.
- Commit to activate travis.
- Updated setup information.
- Replaced template name with crystal17.

  Step 3 of https://aiida-core.readthedocs.io/en/latest/developer_guide/plugins/quickstart.html.
- Added plugin template from https://github.com/aiidateam/aiida-plugin-
  template/archive/master.
- Initial commit.
