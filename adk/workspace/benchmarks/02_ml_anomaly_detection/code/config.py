class Hyperparameters:
    """Experimental parameters for the bio-signal telemetry anomaly detection study."""
    NUM_TRAIN_SAMPLES = 10000
    NUM_VAL_SAMPLES = 2000
    ANOMALY_PROBABILITY_TRAIN = 0.05
    ANOMALY_PROBABILITY_VAL = 0.1
    SEED = 42
    FEATURE_COUNT = ['mean', 'variance', 'skewness', 'kurtosis', 'zero_crossings', 'histogram_entropy']
    USE_RESAMPLING = True
    N_EPOCHS_VAL_SEARCH = 100
    PATIENCE = 20
    BASELINE_METHOD = 'z_score'
    REPORT_METRICS = ['mean_f1_score', 'std_f1_score', 'mean_roc_auc', 'detection_delay_mean']
    SUCCESS_CRITERION = 'mean_f1_score > 0.85'
