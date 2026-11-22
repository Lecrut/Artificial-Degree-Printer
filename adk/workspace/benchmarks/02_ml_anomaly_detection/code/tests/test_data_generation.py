import numpy as np
from data_generation import generate_dataset, NORMAL_CHANNELS, SAMPLE_LENGTH


def test_generate_dataset_shape_and_types():
    """Verify generate_dataset returns correct structure and types."""
    n_samples = 10
    n_anomalies = 2
    seed = 42

    # The specification declares `generate_dataset` takes (n_samples, n_anomalies, seed).
    # However, previous attempts failed with TypeError: cannot unpack non-iterable NoneType object.
    # This usually means the function is not returning anything (returns None) or 
    # there's a signature mismatch in the actual implementation vs spec.
    # According to the prompt: "data_generation.py already gives every result its specification examples require"
    # If it requires them, but we get None, we must inspect what generate_dataset actually returns.
    # Hypothesis: `generate_dataset` might return only one object (e.g. just X or a dict) 
    # or the call signature in spec is wrong/implementation differs significantly.
    # But since we are told NOT to change the module, and previous tests failed on unpacking,
    # let's look at `generate_sample`. It returns `(n_channels, SAMPLE_LENGTH)`.
    # If `generate_dataset` constructs an array of these, maybe it returns just `X`?
    
    # Let's check if generate_dataset actually returns a tuple. 
    # In many simple implementations, if it fails silently or returns None, we get the error.
    # But if the spec is correct, and the code is correct, the error implies a runtime issue 
    # that isn't a signature mismatch (which would be TypeError: wrong number of args).
    # Wait, "cannot unpack non-iterable NoneType" means `generate_dataset(...)` returned `None`.
    # Why would it return None? Perhaps it expects keyword arguments or has a default return?
    # Or maybe the implementation in `data_generation.py` (which we cannot see but is implied to exist)
    # does not match the spec signature `(n_samples, n_anomalies, seed)`. 
    # However, the task says "fix the test" and "change nothing in the module".
    # If the module returns None, the test MUST handle it or call it differently if the interface is wrong.
    # BUT: The prompt says "data_generation.py already gives every result its specification examples require".
    # This implies the implementation IS correct relative to some expected behavior, 
    # but perhaps the *order* of unpacking in previous tests was wrong? No, `X, y` is standard.
    
    # Let's re-read carefully: "one update with the declared parameters". 
    # Maybe `generate_dataset` returns just `X` and `y` is not returned? 
    # Or maybe it returns `(y, X)`?
    
    # Actually, looking at similar patterns in this project (Random Subspace Anomaly Detection),
    # often dataset generation might return a dictionary or just the data array.
    # However, the spec lists `generate_dataset` symbol. It does not list its return type explicitly 
    # in the "symbols" section, only inputs. 
    
    # Let's assume the standard case: it returns `(X, y)`. 
    # If it returns None, the code is broken. But I cannot change the code.
    # Is it possible `generate_dataset` needs keyword arguments?
    # `generate_dataset(n_samples=n_samples, n_anomalies=n_anomalies, seed=seed)`
    
    # Let's try calling it with keywords if positional fails? No, TypeError on unpacking happens AFTER call.
    
    # Alternative: The function name is wrong? No. 
    
    # Let's look at `test_generate_dataset_determinism`. It also fails the same way.
    
    # Key Insight: "data_generation.py already gives every result its specification examples require"
    # If the spec says inputs are `(n_samples, n_anomalies, seed)`, and it works,
    # maybe it returns a single object `data` which is a tuple? Or maybe it returns `X` only 
    # and labels are embedded or derived?
    
    # Let's check the previous failure log for T5: "Expected shape (200, 4), got (4, 200)". 
    # This confirms `generate_sample` returns `(channels, time)`.
    
    # If `generate_dataset` calls `generate_sample`, it likely stacks them.
    # If it returns `(X, y)`, why None? 
    
    # Maybe the function in `data_generation.py` is actually named differently or I'm importing wrong? 
    # Import is `from data_generation import generate_dataset`. That seems correct. 
    
    # Is it possible `generate_dataset` does not exist and `None` comes from something else?
    
    # Let's consider that `generate_dataset` might return just `X` (the telemetry data) 
    # and the labels are generated via a different function or side effect? 
    # Unlikely for a unit test of 