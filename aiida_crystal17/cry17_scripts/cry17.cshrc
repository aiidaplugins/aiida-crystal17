########################################################################
# These commands set up for use of CRYSTAL17.  
# They should be source'd into each CRYSTAL17 user's .cshrc file, 
# after definition of the following environment variable:
#
# User defined variables:
#
# CRY17_ROOT -- CRYSTAL17 main directory. For instance: 
 setenv CRY17_ROOT "/home/CRYSTAL17/"
#
# CRY17_BIN -- directory with executables 
 setenv CRY17_BIN "bin"
#
# CRY17_ARCH -- string defining the platform/compiler
 setenv CRY17_ARCH "Linux-ifort"
#
# VERSION -- string associated with the binary version
 setenv VERSION "std"
#
# CRY17_SCRDIR -- directory scratch (integrals and temporary files)
 setenv CRY17_SCRDIR "$HOME/tmp"
#
# The following variables are according to CRYSTAL17 filesystem structure
 setenv CRY17_EXEDIR "$CRY17_ROOT/$CRY17_BIN/$CRY17_ARCH"
 setenv CRY17_UTILS "$CRY17_ROOT/utils17"
 setenv CRY2K6_GRA "$CRY17_ROOT/crgra2006"
 setenv CRY17_TEST "$CRY17_ROOT/test_cases/inputs"
 setenv GRA6_EXEDIR "$CRY2K6_GRA/bin/Linux-pgf"
#
 setenv PATH "${PATH}:./:${CRY17_EXEDIR}:${CRY17_UTILS}:${CRY2K6_GRA}:${GRA6_EXEDIR}"
#
 echo CRY17_SCRDIR - scratch directory "("integrals and temp files")": $CRY17_SCRDIR
 echo CRY17_EXEDIR - directory with crystal executables: $CRY17_EXEDIR
 echo CRY17_UTILS - running scripts and misc: $CRY17_UTILS/runcry17, runprop17
 echo CRY2K6_GRA - graphical scripts: $CRY2K6_GRA/maps06, doss06, band06
 echo CRY17_TEST - directory with test cases: $CRY17_TEST
#
########################################################################
#  Tip:
#  add the following line in .cshrc file
#
#   source ~/.cry17.cshrc
########################################################################
