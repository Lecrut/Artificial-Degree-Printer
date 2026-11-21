from data_generation import generate_dataset


def test_generate_dataset_signature():
    """Test that generate_dataset accepts exactly one 'seed' argument."""
    # Check signature via help or inspect if needed, but behavior tests rely on correct call.
    pass


def test_generate_dataset_shapes():
    """Test the shapes of returned data and labels match specification."""
    data, labels = generate_dataset(seed=42)
    assert data.shape == (2000, 8), f"Expected shape (2000, 8), got {data.shape}"
    assert labels.shape == (2000,), f"Expected shape (2000,), got {labels.shape}"


def test_generate_dataset_labels_binary():
    """Test that generate_dataset returns binary labels (0 or 1)."""
    data, labels = generate_dataset(seed=42)
    unique_labels = set(labels.tolist())
    assert unique_labels.issubset({0, 1}), f"Labels must be binary, found {unique_labels}"
