from collections import namedtuple
import numpy as np
import pytest

from aiida.orm import ArrayData, Float, List, Dict

from aiida_crystal17.common import recursive_round
from aiida_crystal17.calcfunctions.band_gap import calculate_band_gap, calcfunction_band_gap

TestData = namedtuple(
    'TestData', ['energies', 'densities', 'left_edge', 'right_edge', 'fermi', 'try_fshifts'])


def get_test_data(name):
    fermi = 0.
    try_fshifts = ()

    if name == "zero":
        energies = np.linspace(-1.00, 1.00, num=100)
        densities = np.zeros(100, float)
        left_edge = right_edge = np.nan
    elif name == "non-zero":
        energies = np.linspace(-1.00, 1.00, num=100)
        densities = np.ones(100, float)
        left_edge = right_edge = np.nan
    elif name == "no-left":
        energies = np.linspace(-0.5, 0.5, num=100)
        densities = np.zeros(70, float).tolist() + np.ones(30, float).tolist()
        left_edge = np.nan
        right_edge = 0.20707070707070718
    elif name == "no-right":
        energies = np.linspace(-0.5, 0.5, num=100)
        densities = np.ones(30, float).tolist() + np.zeros(70, float).tolist()
        left_edge = -0.20707070707070707
        right_edge = np.nan
    elif name == "normal":
        energies = np.linspace(-0.5, 0.5, num=100)
        densities = np.ones(20, float).tolist() + np.zeros(60, float).tolist() + np.ones(20, float).tolist()
        left_edge = -0.30808080808080807
        right_edge = 0.30808080808080807
    elif name == "edge_at_fermi":
        # band gap with left edge at fermi (from troilite) but,
        # because of finite steps, the left band edge is just right of the fermi
        energies = np.linspace(-4.99997712, -2.00399482, 300)
        densities = [
            306.226,  310.522,  321.075,  343.847,  378.872,
            420.625,  460.635,  490.813,  506.239,  506.578,
            495.953,  481.488,  471.067,  470.982,  484.073,
            508.816,  539.552,  567.774,  584.177,  601.327,
            721.875,  782.436,  761.426,  682.304,  578.756,
            495.487,  439.913,  441.995,  461.491,  475.672,
            490.718,  506.736,  538.117,  587.377,  642.053,
            695.22,  700.75,  639.65,  523.2,  452.914,
            492.114,  594.729,  721.793,  790.935,  806.407,
            838.359,  710.906,  578.175,  488.674,  505.66,
            542.658,  568.484,  543.19,  441.902,  229.896,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    2.12092,  121.3696,  159.7785,
            229.503,  250.007,  401.783,  474.58,  701.426,
            1248.691, 1591.101, 1545.552, 1925.306, 1379.782,
            772.587,   23.4285,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,    0.,    0.,    0.,
            0.,    0.,  306.77,  586.228,  712.117,
            738.386,  713.274,  643.258,  629.585,  762.91,
            998.339, 1116.738, 1078.882,  945.859,  861.712,
            899.015,  935.442,  878.698,  930.871,  891.244,
            767.356,  696.475,  669.919,  712.856,  778.554,
            792.925,  714.388,  582.563,  452.37,  373.857,
            347.046,  319.079,  320.468,  353.079,  395.78,
            450.184,  527.969,  673.726,  867.459, 1010.925,
            1014.193,  853.558,  602.265,  386.996,  295.081]
        fermi = -4.4561093632492
        try_fshifts = [0.01]
        left_edge, right_edge = (-4.458896704615384, -3.0260356046153847)
    else:
        raise ValueError(name)

    return TestData(energies, densities, left_edge, right_edge, fermi, try_fshifts)


@pytest.mark.parametrize('dtype', ("zero", "non-zero", "no-left", "no-right",
                                   "normal", "edge_at_fermi"))
def test_band_gap(dtype):
    data = get_test_data(dtype)
    result = calculate_band_gap(
        data.energies, data.densities, missing_edge=np.nan,
        fermi=data.fermi, try_fshifts=data.try_fshifts)
    assert result.left_edge == pytest.approx(data.left_edge, nan_ok=True)
    assert result.right_edge == pytest.approx(data.right_edge, nan_ok=True)


def test_calcfunction_band_gap(db_test_app, data_regression):
    data = get_test_data("edge_at_fermi")
    array = ArrayData()
    array.set_array('energies', np.array(data.energies))
    array.set_array('total', np.array(data.densities))
    outputs, node = calcfunction_band_gap.run_get_node(
        doss_array=array,
        doss_results=Dict(dict={"fermi_energy": data.fermi, "energy_units": "eV"}),
        dtol=Float(1e-6),
        try_fshifts=List(list=data.try_fshifts),
        metadata={'store_provenance': True})
    assert node.is_finished_ok, node.exit_status
    assert "results" in node.outputs
    data_regression.check(recursive_round(node.outputs.results.attributes, 4))


def test_calcfunction_band_gap_with_spin(db_test_app, data_regression):
    data = get_test_data("edge_at_fermi")
    array = ArrayData()
    array.set_array('energies', np.array(data.energies))
    array.set_array('total_alpha', np.array(data.densities))
    array.set_array('total_beta', np.array(data.densities))
    outputs, node = calcfunction_band_gap.run_get_node(
        doss_array=array,
        doss_results=Dict(dict={"fermi_energy": data.fermi, "energy_units": "eV"}),
        dtol=Float(1e-6),
        try_fshifts=List(list=data.try_fshifts),
        metadata={'store_provenance': True})
    assert node.is_finished_ok, node.exit_status
    assert "results" in node.outputs
    data_regression.check(recursive_round(node.outputs.results.attributes, 4))
