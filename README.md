# aiida-crystal17

AiiDA plugin for running the [CRYSTAL17](http://www.crystal.unito.it/) code

# Installation

```shell
git clone https://github.com/chrisjsewell/aiida-crystal17 .
cd aiida-crystal17
pip install -e .  # also installs aiida, if missing (but not postgres)
#pip install -e .[precommit,testing] # install extras for more features
verdi quicksetup  # better to set up a new profile
verdi calculation plugins  # should now show your calclulation plugins
```

# Usage

Here goes a complete example of how to submit a test calculation using this plugin.


# Development and Testing Notes

The original plugin template was created from the 
[aiida-plugin-cutter
](https://github.com/aiidateam/aiida-plugin-cutter/tree/e614256377a4ac0c03f0ffca1dfe7bd9bb618983).

## Testing against mock CRYSTAL17 executables

Because CRYSTAL17 is a licensed software, it is not possible to source a copy of the executable on Travis CI.
Therefore, a mock executable (`mock_runcry17`) has been created for testing purposes (which also speeds up test runs). 

This executable computes the md5 hash of the supplied input file and tries to match it against a dictionary of 
precomputed hashes. If found, the executable will write the matching output (from `test/output_files`) to stdout.

To use this mock executable when running tests, set the global variable `MOCK_CRY_EXECUTABLES=true`.

## Setting up CRYSTAL17 locally

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


# License

MIT

# Contact

chrisj_sewell@hotmail.com
