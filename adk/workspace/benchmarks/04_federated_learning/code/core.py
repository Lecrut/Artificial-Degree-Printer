import csv
import math
import os
import numpy as np
from typing import Tuple, List, Optional, Dict, Any

# -----------------------------------------------------------------------------
# Module Constants & Configuration References (Semantic Links)
# -----------------------------------------------------------------------------
# These constants mirror the definitions in config.py for local reproducibility.
NUM_CLIENTS: int = 10
DIRICHLET_ALPHA: float = 0.5
LOCAL_EPOCHS: int = 3
LEARNING_RATE: float = 0.05
MU_PROXIMAL: float = 0.01
ROUNDS: int = 25
STRAGGLER_RATE: float = 0.25  # 25% client dropout rate
SEED: int = 42


def generate_federated_partitions(
    n_samples: int,
    n_clients: int,
    alpha: float,
    seed: int = 42
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """
    Generate synthetic non-IID data partitions for Federated Learning using Dirichlet distribution.

    Algorithm:
        1. Sample label proportions from a Dirichlet distribution \text{Dir}(\alpha)
           for each client to control the degree of non-IIDness.
        2. Assign samples to clients based on these proportions.
        3. Generate synthetic features and labels (multinomial classification) deterministically.

    Args:
        n_samples: Total number of synthetic data points to generate.
        n_clients: Number of federated clients.
        alpha: Dirichlet concentration parameter. Lower alpha implies more non-IID data.
               \alpha \rightarrow 0 results in extremely skewed distributions.
        seed: Random seed for reproducibility.

    Returns:
        A tuple (client_X, client_y) where:
        - client_X is a list of np.ndarray arrays containing input features for each client.
        - client_y is a list of np.ndarray arrays containing corresponding labels for each client.
        The sum of all client samples equals n_samples.

    Complexity:
        Time: O(n_samples * n_features) for generation, O(n_clients * n_samples) for partitioning.
        Space: O(n_samples * n_features) to store the dataset.
    """
    if alpha <= 0:
        raise ValueError("Dirichlet parameter alpha must be strictly positive.")

    rng = np.random.default_rng(seed)
    
    # Synthetic classification parameters
    n_classes: int = 10
    n_features: int = 20
    
    # 1. Generate class proportions for each client using Dirichlet distribution
    # Each row of dirichlet_p contains the probability distribution over classes for that client
    dirichlet_p: np.ndarray = rng.dirichlet(alpha=np.ones(n_classes) * alpha, size=n_clients)
    
    # 2. Assign samples to clients
    # We allocate n_samples/n_clients roughly, but adjust based on dirichlet proportions
    # To ensure exact sum of samples == n_samples, we use cumulative rounding trick or multinomial
    client_counts: List[int] = rng.multinomial(n_samples, dirichlet_p.sum(axis=1) / dirichlet_p.sum()).astype(int)
    
    # Ensure no client gets 0 samples if possible, though Dirichlet allows it
    if np.any(client_counts == 0):
        # Remsample those with zero counts from remaining pool (simple re-balancing)
        missing_idx = np.where(client_counts == 0)[0]
        remaining_samples = n_samples - client_counts.sum()
        # Fallback: distribute remaining evenly
        for idx in missing_idx:
            client_counts[idx] = max(1, int(n_samples / n_clients) // 2)
    
    # Recalculate counts to sum exactly to n_samples if drift occurred
    diff = n_samples - np.sum(client_counts)
    if diff != 0:
        client_counts[0] += diff

    # Initialize storage
    all_X: List[np.ndarray] = []
    all_y: List[np.ndarray] = []
    
    for i in range(n_clients):
        n_i = client_counts[i]
        if n_i == 0:
            continue
            
        # Generate samples for this client based on its specific class distribution
        # Sample indices from the global uniform distribution, weighted by dirichlet_p[i]
        class_probs = dirichlet_p[i]
        class_labels_local = rng.choice(n_classes, size=n_i, p=class_probs)
        
        # Generate synthetic features (multinormal around class means)
        # Simplified: Random normal noise + deterministic class centroid
        client_X: np.ndarray = rng.normal(loc=0.0, scale=1.0, size=(n_i, n_features))
        for c in range(n_classes):
            mask = (class_labels_local == c)
            if np.any(mask):
                # Add a small shift to distinguish classes
                client_X[mask] += np.eye(n_features)[c % n_features] * 0.5 
        
        all_X.append(client_X)
        all_y.append(class_labels_local)

    return all_X, all_y


def client_local_train(
    weights: np.ndarray,
    bias: float,
    client_X: np.ndarray,
    client_y: np.ndarray,
    epochs: int = LOCAL_EPOCHS,
    lr: float = LEARNING_RATE,
    mu: float = MU_PROXIMAL
) -> Tuple[np.ndarray, float]:
    """
    Perform local Stochastic Gradient Descent (SGD) optimization with Proximal Loss regularization.

    This function simulates the client-side training step in a Federated Learning round.
    It updates local model parameters by minimizing the empirical loss plus a proximal
    term that penalizes deviation from the global model weights. This regularizer helps
    mitigate client drift, especially under Non-IID data distributions \cite{Li2020FedProx}.

    Proximal Loss Formulation:
        L_{prox}(w) = L_{local}(w) + \frac{\mu}{2} ||w - w_{global}||^2

    Args:
        weights: Current global model weight vector (np.ndarray).
                 Used as the reference point for the proximal term.
        bias: Current global model bias scalar.
              Note: For simplicity in this pure Python simulation, bias regularization 
              is omitted or implicitly handled if included in 'weights'. Here we assume
              weights are shape (n_features,) and bias is separate.
        client_X: Local client input feature matrix (np.ndarray) of shape (n_samples, n_features).
        client_y: Local client label vector (np.ndarray) of shape (n_samples,).
        epochs: Number of local training epochs for this client. Defaults to \ref_ast{config.py:LOCAL_EPOCHS}.
        lr: Learning rate for SGD updates. Defaults to \ref_ast{config.py:LEARNING_RATE}.
        mu: Proximal regularization parameter (\mu). Controls the strength of the penalty
            for deviating from the global model. Defaults to \ref_ast{config.py:MU_PROXIMAL}.

    Returns:
        A tuple (updated_weights, updated_bias) where:
        - updated_weights: np.ndarray representing the client's local weight updates.
        - updated_bias: float representing the client's local bias update.

    Complexity:
        Time: O(epochs * n_samples * n_features) for gradient computation and updates.
        Space: O(n_features) for storing gradients and intermediate vectors.
    """
    # Initialize local weights with a copy of global weights to track deviation
    local_w = weights.copy()
    local_b = bias
    
    n_samples, n_features = client_X.shape
    rng = np.random.default_rng(SEED) # Deterministic local seed for mini-batch sampling
    
    for epoch in range(epochs):
        # Shuffle data indices for this epoch
        indices = rng.permutation(n_samples)
        X_shuffled = client_X[indices]
        y_shuffled = client_y[indices]
        
        # Mini-batch SGD (using full batch here for stability/determinism in simulation,
        # or small batches if performance permits. Pure Python loop below.
        # For efficiency in this context, we treat the whole client dataset as one batch per epoch
        # to minimize overhead and ensure deterministic convergence paths).
        
        # Forward Pass: Linear Model
        predictions = np.dot(X_shuffled, local_w) + local_b
        
        # Loss Calculation (Mean Squared Error for regression proxy, or Cross-Entropy logic adapted)
        # Assuming binary classification or regression target for simplicity in pure NumPy without softplus overhead.
        # Let's assume a regression task for weight update stability in this synthetic setup,
        # or use a simplified hinge-like gradient for classification robustness.
        # Standard MSE loss gradient: grad = (1/N) * sum((pred - true) * X)
        error = predictions - y_shuffled
        
        # Gradient of Empirical Loss
        grad_w_empirical = (1.0 / n_samples) * np.dot(X_shuffled.T, error)
        grad_b_empirical = (1.0 / n_samples) * np.sum(error)
        
        # Gradient of Proximal Term: \mu * (w_{local} - w_{global})
        prox_grad_w = mu * (local_w - weights)
        prox_grad_b = mu * (local_b - bias)
        
        # Combined Gradient
        grad_w_total = grad_w_empirical + prox_grad_w
        grad_b_total = grad_b_empirical + prox_grad_b
        
        # SGD Update Step
        local_w -= lr * grad_w_total
        local_b -= lr * grad_b_total

    return local_w, local_b


def train_and_evaluate(
    csv_out_path: str = "results.csv",
    seed: int = SEED
) -> Dict[str, Any]:
    """
    Simulate the full Federated Learning lifecycle comparing FedAvg vs. Adaptive FedProx.

    This function orchestrates the global training loop, client partitioning, local training,
    and server-side aggregation. It simulates straggler dropout (25% clients failing to update)
    and calculates key performance metrics including convergence speed, accuracy, communication
    overhead, and resilience rates.

    Args:
        csv_out_path: Path to save the results CSV table.
        seed: Global random seed for reproducibility.

    Returns:
        A dictionary containing calculated metrics:
        - 'convergence_rounds': int
        - 'final_accuracy': float
        - 'communication_overhead_kb': float
        - 'straggler_resilience_rate': float
        - 'divergence_rate': float
    """
    rng = np.random.default_rng(seed)
    
    # --- Configuration & Initialization ---
    n_clients: int = NUM_CLIENTS
    n_rounds: int = ROUNDS
    n_samples_total: int = 10000
    n_classes: int = 10
    n_features: int = 20
    
    # Initialize global model parameters (Random Small Initialization)
    global_w: np.ndarray = rng.normal(0, 0.01, size=n_features)
    global_b: float = 0.0
    
    # --- Data Partitioning (Non-IID) ---
    client_X_list, client_y_list = generate_federated_partitions(
        n_samples=n_samples_total,
        n_clients=n_clients,
        alpha=DIRICHLET_ALPHA,
        seed=seed
    )
    
    # Metric Storage
    history_fedavg_acc: List[float] = []
    history_fedprox_acc: List[float] = []
    communication_rounds: int = 0
    total_data_kb_transferred: float = 0.0
    straggler_count: int = 0
    successful_updates_prox: int = 0
    successful_updates_avg: int = 0
    
    # --- Federated Learning Loop ---
    for round_idx in range(n_rounds):
        # 1. Select Active Clients (Simulate 25% Straggler Dropout)
        # In FedProx, stragglers are handled gracefully by excluding them from the weighted average
        active_clients: List[int] = []
        for c_id in range(n_clients):
            # Simulate dropout probability
            if rng.random() > STRAGGLER_RATE:
                active_clients.append(c_id)
            else:
                straggler_count += 1
        
        # If no clients are active, skip round to prevent division by zero/empty updates
        if not active_clients:
            continue
        
        # Calculate number of participants for weight averaging
        n_participants = len(active_clients)
        
        # --- Baseline: FedAvg (Mu = 0) ---
        # Aggregate weights from active clients
        fedavg_w_list: List[np.ndarray] = []
        fedavg_b_list: List[float] = []
        local_n_samples_avg: List[int] = []
        
        for c_id in active_clients:
            client_X, client_y = client_X_list[c_id], client_y_list[c_id]
            n_local = len(client_y)
            
            # Train locally with FedAvg (mu=0 implicitly via call or separate function)
            # Here we reuse client_local_train by passing mu=0
            local_w, local_b = client_local_train(
                weights=global_w,
                bias=global_b,
                client_X=client_X,
                client_y=client_y,
                epochs=LOCAL_EPOCHS,
                lr=LEARNING_RATE,
                mu=0.0
            )
            fedavg_w_list.append(local_w)
            fedavg_b_list.append(local_b)
            local_n_samples_avg.append(n_local)
        
        # Server Aggregation (FedAvg: Weighted Average by sample size)
        total_samples_avg = sum(local_n_samples_avg)
        if total_samples_avg > 0:
            avg_w_num = np.zeros_like(global_w)
            avg_b_denom = 0
            for i, c_id in enumerate(active_clients):
                w_local = fedavg_w_list[i]
                n_i = local_n_samples_avg[i]
                b_local = fedavg_b_list[i]
                
                # Weighted sum
                avg_w_num += (n_i / total_samples_avg) * w_local
                avg_b_denom += (n_i / total_samples_avg) * b_local
            
            global_w_fedavg = avg_w_num
            global_b_fedavg = avg_b_denom
        else:
            global_w_fedavg = global_w
            global_b_fedavg = global_b
            straggler_count += n_clients # All failed as none active
        
        successful_updates_avg += n_participants
        
        # --- Proposed: Adaptive FedProx (Mu > 0) ---
        fedprox_w_list: List[np.ndarray] = []
        fedprox_b_list: List[float] = []
        local_n_samples_prox: List[int] = []
        
        for c_id in active_clients:
            client_X, client_y = client_X_list[c_id], client_y_list[c_id]
            n_local = len(client_y)
            
            # Train locally with FedProx (mu=MU_PROXIMAL)
            local_w, local_b = client_local_train(
                weights=global_w,
                bias=global_b,
                client_X=client_X,
                client_y=client_y,
                epochs=LOCAL_EPOCHS,
                lr=LEARNING_RATE,
                mu=MU_PROXIMAL
            )
            fedprox_w_list.append(local_w)
            fedprox_b_list.append(local_b)
            local_n_samples_prox.append(n_local)
        
        # Server Aggregation (FedProx: Standard Weighted Average, but regularized locally)
        total_samples_prox = sum(local_n_samples_prox)
        if total_samples_prox > 0:
            avg_w_num = np.zeros_like(global_w)
            avg_b_denom = 0
            for i, c_id in enumerate(active_clients):
                w_local = fedprox_w_list[i]
                n_i = local_n_samples_prox[i]
                b_local = fedprox_b_list[i]
                
                avg_w_num += (n_i / total_samples_prox) * w_local
                avg_b_denom += (n_i / total_samples_prox) * b_local
            
            global_w_fedprox = avg_w_num
            global_b_fedprox = avg_b_denom
        else:
            global_w_fedprox = global_w
            global_b_fedprox = global_b
        
        successful_updates_prox += n_participants
        
        # --- Communication Overhead Calculation ---
        # Size of weights (float64) + bias (float64) per round transfer
        param_size_bytes = (n_features * 8) + 8 
        # Roundtrip: Client upload + Server broadcast
        overhead_kb = (2 * n_participants * param_size_bytes) / 1024
        total_data_kb_transferred += overhead_kb
        communication_rounds += 1
        
        # --- Evaluation on Held-out Test Set (Synthetic) ---
        # Generate a test set with IID distribution for fair comparison
        test_X, test_y = generate_federated_partitions(
            n_samples=2000,
            n_clients=1, # Single 'server' node generating IID data
            alpha=DIRICHLET_ALPHA * 10, # High alpha approximates IID
            seed=seed + 100
        )
        test_X, test_y = test_X[0], test_y[0]
        
        def calculate_accuracy(w: np.ndarray, b: float, X: np.ndarray, y: np.ndarray) -> float:
            preds = np.argmax(np.dot(X, w) + b, axis=1)
            # Assuming multi-class classification accuracy
            return float(np.mean(preds == y))
        
        acc_fedavg = calculate_accuracy(global_w_fedavg, global_b_fedavg, test_X, test_y)
        acc_fedprox = calculate_accuracy(global_w_fedprox, global_b_fedprox, test_X, test_y)
        
        history_fedavg_acc.append(acc_fedavg)
        history_fedprox_acc.append(acc_fedprox)
        
        # Update Global Model State for next round (use FedProx as the 'proposed' standard for state, 
        # or FedAvg depending on which model is being tracked. Usually, we track the best one.
        # Here we advance both parallel states).
        global_w = global_w_fedprox 
        global_b = global_b_fedprox

    # --- Final Metrics Calculation ---
    final_acc_prox: float = history_fedprox_acc[-1] if history_fedprox_acc else 0.0
    final_acc_avg: float = history_fedavg_acc[-1] if history_fedavg_acc else 0.0
    
    # Straggler Resilience: Ratio of rounds where sufficient updates were received to complete aggregation
    max_possible_stragglers_per_round = n_clients * STRAGGLER_RATE
    # Defined as: successful_updates / potential_updates (simplified metric)
    total_participants_observed = successful_updates_prox + straggler_count 
    resilience_rate: float = successful_updates_prox / total_participants_observed if total_participants_observed > 0 else 0.0
    
    # Divergence Rate: Measure of weight oscillation between rounds for FedAvg vs FedProx
    # Simplified: Variance of accuracy difference in final 5 rounds
    if len(history_fedavg_acc) >= 5 and len(history_fedprox_acc) >= 5:
        diff_final = [abs(a - b) for a, b in zip(history_fedavg_acc[-5:], history_fedprox_acc[-5:])]
        divergence_rate: float = float(np.std(diff_final))
    else:
        divergence_rate = 0.0

    # --- CSV Output ---
    os.makedirs(os.path.dirname(csv_out_path) if os.path.dirname(csv_out_path) else '.', exist_ok=True)
    with open(csv_out_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['baseline', 'convergence_rounds', 'final_accuracy', 'communication_overhead_kb', 'straggler_resilience_rate', 'divergence_rate'])
        writer.writerow(['baseline', communication_rounds, final_acc_avg, total_data_kb_transferred, resilience_rate, divergence_rate])
        writer.writerow(['proposed', communication_rounds, final_acc_prox, total_data_kb_transferred, resilience_rate, divergence_rate])

    return {
        "convergence_rounds": communication_rounds,
        "final_accuracy": final_acc_prox,
        "communication_overhead_kb": total_data_kb_transferred,
        "straggler_resilience_rate": resilience_rate,
        "divergence_rate": divergence_rate
    }