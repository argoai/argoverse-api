# <Copyright 2020, Argo AI, LLC. Released under the MIT license.>
"""Detection evaluation unit tests"""

import logging
import pathlib

import numpy as np
import pytest
from pandas.core.frame import DataFrame
from scipy.spatial.transform import Rotation as R

from argoverse.data_loading.object_label_record import ObjectLabelRecord
from argoverse.evaluation.detection_utils import DistFnType, SimFnType, compute_match_matrix, dist_fn
from argoverse.evaluation.eval_detection import DetectionCfg, DetectionEvaluator
from argoverse.utils.transform import quat_scipy2argo_vectorized

TEST_DATA_LOC = pathlib.Path(__file__).parent.parent / "tests" / "test_data" / "detection"
logging.getLogger("matplotlib.font_manager").disabled = True


@pytest.fixture
def evaluator() -> DetectionEvaluator:
    """Define an evaluator that compares a set of results to itself."""
    detection_cfg = DetectionCfg(significant_digits=32)
    return DetectionEvaluator(
        TEST_DATA_LOC / "detections", TEST_DATA_LOC, TEST_DATA_LOC / "test_figures", detection_cfg
    )


@pytest.fixture
def metrics(evaluator: DetectionEvaluator) -> DataFrame:
    return evaluator.evaluate()


def test_center_similarity() -> None:
    """Test that the Center similarity function works."""
    olr1 = np.array([ObjectLabelRecord(np.array([0, 0, 0, 0]), np.array([0, 0, 0]), 5.0, 5.0, 5.0, 0)])
    olr2 = np.array([ObjectLabelRecord(np.array([0, 0, 0, 0]), np.array([3, 4, 0]), 5.0, 5.0, 5.0, 0)])
    assert compute_match_matrix(olr1, olr2, SimFnType.CENTER) == -5


def test_translation_distance() -> None:
    """Test that the translation distance function works."""
    df1 = DataFrame([{"translation": [0.0, 0.0, 0.0]}])
    df2 = DataFrame([{"translation": [5.0, 5.0, 5.0]}])
    assert dist_fn(df1, df2, DistFnType.TRANSLATION) == 75 ** (1 / 2)


def test_scale_distance() -> None:
    """Test that the scale distance function works."""
    df1 = DataFrame([{"width": 5, "height": 5, "length": 5}])
    df2 = DataFrame([{"width": 10, "height": 10, "length": 10}])
    assert (dist_fn(df1, df2, DistFnType.SCALE) == 1 - 0.125).all()


def test_orientation_distance() -> None:
    """Test that the orientation distance function works."""
    # check all of the 45 degree angles
    vecs_45_apart = [angle * np.array([0, 0, 1]) for angle in np.arange(0, 2 * np.pi, np.pi / 4)]
    for i in range(len(vecs_45_apart) - 1):
        df1 = DataFrame([{"quaternion": quat_scipy2argo_vectorized(R.from_rotvec(vecs_45_apart[i]).as_quat())}])
        df2 = DataFrame([{"quaternion": quat_scipy2argo_vectorized(R.from_rotvec(vecs_45_apart[i + 1]).as_quat())}])
        assert np.isclose(dist_fn(df1, df2, DistFnType.ORIENTATION), np.pi / 4)
        assert np.isclose(dist_fn(df2, df1, DistFnType.ORIENTATION), np.pi / 4)
    # check all of the 90 degree angles
    vecs_90_apart = [angle * np.array([0, 0, 1]) for angle in np.arange(0, 2 * np.pi, np.pi / 2)]
    for i in range(len(vecs_90_apart) - 1):
        df1 = DataFrame([{"quaternion": quat_scipy2argo_vectorized(R.from_rotvec(vecs_90_apart[i]).as_quat())}])
        df2 = DataFrame([{"quaternion": quat_scipy2argo_vectorized(R.from_rotvec(vecs_90_apart[i + 1]).as_quat())}])
        assert np.isclose(dist_fn(df1, df2, DistFnType.ORIENTATION), np.pi / 2)
        assert np.isclose(dist_fn(df2, df1, DistFnType.ORIENTATION), np.pi / 2)


def test_ap(metrics: DataFrame) -> None:
    """Test that AP is 1 for the self-compared results."""
    assert metrics.AP.Means == 1


def test_translation_error(metrics: DataFrame) -> None:
    """Test that ATE is 0 for the self-compared results."""
    assert metrics.ATE.Means == 0


def test_scale_error(metrics: DataFrame) -> None:
    """Test that ASE is 0 for the self-compared results."""
    assert metrics.ASE.Means == 0


def test_orientation_error(metrics: DataFrame) -> None:
    """Test that AOE is 0 for the self-compared results."""
    assert metrics.AOE.Means == 0
