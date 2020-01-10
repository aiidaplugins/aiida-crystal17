from textwrap import dedent

from aiida_crystal17.parsers.raw.crystal_ppan import parse_crystal_ppan


def test_read_doss_contents_spin1(data_regression):
    contents = dedent("""\
        # Mulliken Populations:
        # NSPIN,NATOM
        # IAT,NSHELL
        # Xiat,Yiat,Ziat (AU)
        # QTOT shell charges
        # NORB
        # orbital charges
                1          2
                12          3
            0.000     0.000     0.000
            11.223     1.999     7.622     1.602
                9
            1.999     1.961     1.887     1.887     1.887     0.549     0.351     0.351
            0.351
                8          2
            3.978    -3.978     3.978
            8.777     1.998     6.779
                18
            2.000     1.999     1.999     1.999     1.999     1.997     1.973     1.973
            1.974     1.102     0.501     0.501     0.628     1.001     1.992     1.992
            0.999     1.007
    """)
    data_regression.check(parse_crystal_ppan(contents))


def test_read_doss_contents_spin2(data_regression):
    contents = dedent("""\
        # Mulliken Populations:
        # NSPIN,NATOM
        # IAT,NSHELL
        # Xiat,Yiat,Ziat (AU)
        # QTOT shell charges
        # NORB
        # orbital charges
                2          1
                12          3
            0.000     0.000     0.000
            11.223     1.999     7.622     1.602
                9
            1.999     1.961     1.887     1.887     1.887     0.549     0.351     0.351
            0.351
                8          2
            3.978    -3.978     3.978
            8.777     1.998     6.779
                5
            1.998     1.867     1.637     1.637     1.637
    """)
    data_regression.check(parse_crystal_ppan(contents))
