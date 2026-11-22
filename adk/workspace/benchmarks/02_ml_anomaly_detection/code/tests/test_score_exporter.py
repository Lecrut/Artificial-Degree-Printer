from score_exporter import OUTPUT_DIR, OUTPUT_FILENAME, export_scores
import numpy as np

def test_export_scores_signature_and_outputs():
    """Test the exported function signature and data type invariants."""
    import numpy as np
    dataset_y_true = np.array([0.5, 1.2, 3.8])
    baseline_scores = np.array([0.1, 0.9, 2.3])
    subspace_scores = np.array([0.2, 1.0, 2.4])
    result = export_scores(dataset_y_true, baseline_scores)
    if result is None:
        import os
        expected_path = os.path.join(str(OUTPUT_DIR), str(OUTPUT_FILENAME))
        if not os.path.exists(expected_path):
            raise AssertionError(f"Expected output file '{expected_path}' was not created by export_scores().")
    else:
        raise AssertionError('Function should return None on success or structured data; unexpected non-None value: {}'.format(result))
    assert OUTPUT_DIR is not None and isinstance(OUTPUT_DIR, str), 'OUTPUT_DIR must be a non-empty string'
    assert OUTPUT_FILENAME is not None and isinstance(OUTPUT_FILENAME, str), 'OUTPUT_FILENAME must be a non-empty string'
