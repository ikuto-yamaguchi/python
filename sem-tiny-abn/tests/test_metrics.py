from sem_tiny_abn.metrics import calibrate_ok_threshold


def test_threshold_calibration_can_force_zero_false_ok():
    result = calibrate_ok_threshold([0, 0, 1, 1], [0.95, 0.80, 0.70, 0.20], ok_index=0, target_false_ok_rate=0.0)
    assert result["false_ok_rate"] == 0.0
    assert result["threshold"] > 0.70
