from textwrap import dedent
from aiida_crystal17.parsers.raw.doss import (
    read_doss_contents, create_doss_content)


def test_read_doss_contents(data_regression):
    contents = dedent("""\
    NEWK
    18 36
    1 0
    DOSS
    7 1000 29 55 1 14 0
    12 1 2 3 4 5 6 41 42 43 44 45 46
    24 7 8 9 10 11 12 13 14 15 16 17 18 47 48 49 50 51 52 53 54 55 56 57 58
    30 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73
    14 34 35 36 37 38 39 40 74 75 76 77 78 79 80
    10 81 82 83 84 85 103 104 105 106 107
    24 86 87 88 89 90 91 92 93 94 95 96 97 108 109 110 111 112 113 114 115 116 117 118 119
    10 98 99 100 101 102 120 121 122 123 124
    END
    """)
    data_regression.check(read_doss_contents(contents))


def test_create_doss_content(file_regression):
    params = {
        "shrink_is": 18,
        "shrink_isp": 36,
        # "npro": 7,
        "npt": 1000,
        "band_first": 29,
        "band_last": 55,
        # "iplo": 1,
        "npol": 14,  # <= 25, suggested values for NPOL: 10 to 18
        # "npr": 0,
        "energy_gap": None,  # or [bmin, bmax] in hartree
        "projections": {
            "atoms": None,
            "orbitals": [
                [1, 2, 3, 4, 5, 6, 41, 42, 43, 44, 45, 46],
                [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 47,
                    48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58],
                [19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33,
                    59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73],
                [34, 35, 36, 37, 38, 39, 40, 74, 75, 76, 77, 78, 79, 80],
                [81, 82, 83, 84, 85, 103, 104, 105, 106, 107],
                [86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 108, 109,
                    110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
                [98, 99, 100, 101, 102, 120, 121, 122, 123, 124]
            ]
        }
    }
    file_regression.check("\n".join(create_doss_content(params)))
