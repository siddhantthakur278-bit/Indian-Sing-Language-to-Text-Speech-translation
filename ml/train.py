"""
ISL BiLSTM Baseline Model Training Module
Trains a Bidirectional LSTM network on 30x258 normalized landmark sequences.
"""

import os
import json
import logging
import argparse
import numpy as np
from typing import Tuple, List

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
from sklearn.utils.class_weight import compute_class_weight

from preprocess import normalize, augment_sequence, signer_wise_split
from models import get_model, build_bilstm_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def build_bilstm_model(seq_len: int = 30, feat_dim: int = 258, num_classes: int = 70) -> tf.keras.Model:
    """Constructs the baseline BiLSTM network architecture specified in Section 8.1."""
    inputs = layers.Input(shape=(seq_len, feat_dim), name="landmark_input")
    x = layers.Masking(mask_value=0.0, name="zero_masking")(inputs)
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True, name="bilstm_1"), name="bi_wrapper_1")(x)
    x = layers.Dropout(0.3, name="dropout_1")(x)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=False, name="bilstm_2"), name="bi_wrapper_2")(x)
    x = layers.Dropout(0.3, name="dropout_2")(x)
    x = layers.Dense(128, activation="relu", name="dense_features")(x)
    x = layers.BatchNormalization(name="bn_features")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="class_probabilities")(x)

    model = models.Model(inputs=inputs, outputs=outputs, name="ISL_BiLSTM_Classifier")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    return model


def load_dataset(processed_dir: str, classes_file: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Loads pre-extracted numpy landmark files and labels with missing file checks."""
    if not os.path.exists(classes_file):
        raise FileNotFoundError(f"Classes file '{classes_file}' not found. Please verify file path or run from repo root.")

    with open(classes_file, "r") as f:
        class_meta = json.load(f)
    classes = class_meta.get("classes", [])
    if not classes:
        raise ValueError(f"No classes found in '{classes_file}'.")
    class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}

    if not os.path.exists(processed_dir):
        logger.warning(f"Processed data directory '{processed_dir}' does not exist. Using synthetic mock data.")
        num_mock_samples = len(classes) * 4
        X_mock = np.random.randn(num_mock_samples, 30, 258).astype(np.float32) * 0.1
        y_mock = np.array([i % len(classes) for i in range(num_mock_samples)], dtype=np.int32)
        return X_mock, y_mock, classes

    sequences = []
    labels = []
    file_paths = []

    for cls_name in classes:
        cls_dir = os.path.join(processed_dir, cls_name)
        if not os.path.exists(cls_dir):
            continue

        npy_files = [os.path.join(cls_dir, f) for f in os.listdir(cls_dir) if f.endswith(".npy")]
        for f_path in npy_files:
            try:
                seq = np.load(f_path)
                if seq.shape == (30, 258):
                    norm_seq = normalize(seq)
                    sequences.append(norm_seq)
                    labels.append(class_to_idx[cls_name])
                    file_paths.append(f_path)
            except Exception as e:
                logger.warning(f"Error loading {f_path}: {e}")

    if not sequences:
        logger.warning("No .npy sequences found. Creating synthetic mock data for architecture verification.")
        # Create small mock set with 70 classes
        num_mock_samples = len(classes) * 4
        X_mock = np.random.randn(num_mock_samples, 30, 258).astype(np.float32) * 0.1
        y_mock = np.array([i % len(classes) for i in range(num_mock_samples)], dtype=np.int32)
        return X_mock, y_mock, classes

    return np.array(sequences, dtype=np.float32), np.array(labels, dtype=np.int32), classes


def train(data_dir: str, classes_path: str, output_model: str = "isl_model.keras", epochs: int = 100, batch_size: int = 32, arch: str = "bilstm"):
    """Main model training routine."""
    logger.info(f"Loading data from {data_dir} and classes from {classes_path}...")
    X, y, classes = load_dataset(data_dir, classes_path)
    num_classes = len(classes)
    logger.info(f"Loaded {len(X)} total sequences across {num_classes} classes.")

    # Stratified or randomized 80/10/10 train/val/test split
    indices = np.arange(len(X))
    np.random.seed(42)
    np.random.shuffle(indices)

    n_val = max(1, int(len(X) * 0.15))
    n_test = max(1, int(len(X) * 0.10))
    n_train = len(X) - n_val - n_test

    train_idx = indices[:n_train]
    val_idx = indices[n_train:n_train + n_val]
    test_idx = indices[n_train + n_val:]

    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    logger.info(f"Train split: {len(X_train)}, Val split: {len(X_val)}, Test split: {len(X_test)}")

    model = get_model(arch=arch, seq_len=30, feat_dim=258, num_classes=num_classes)
    model.summary(print_fn=logger.info)

    os.makedirs(os.path.dirname(output_model) or ".", exist_ok=True)

    callbacks_list = [
        callbacks.EarlyStopping(monitor="val_accuracy", patience=12, restore_best_weights=True, verbose=1),
        callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, min_lr=1e-5, verbose=1),
        callbacks.CSVLogger("training_history.csv"),
        callbacks.ModelCheckpoint(output_model, monitor="val_accuracy", save_best_only=True, verbose=1)
    ]

    # Calculate class weights to handle imbalance
    unique_classes = np.unique(y_train)
    if len(unique_classes) > 1:
        weights = compute_class_weight("balanced", classes=unique_classes, y=y_train)
        class_weight_dict = {cls: weight for cls, weight in zip(unique_classes, weights)}
    else:
        class_weight_dict = None

    logger.info("Starting training loop...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        class_weight=class_weight_dict,
        callbacks=callbacks_list,
        verbose=1
    )

    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    logger.info(f"Final Test Evaluation: Loss={test_loss:.4f}, Accuracy={test_acc*100:.2f}%")

    model.save(output_model)
    logger.info(f"Model saved to {output_model}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train ISL BiLSTM model")
    parser.add_argument("--data", type=str, default="data/processed", help="Path to processed sequences")
    parser.add_argument("--classes", type=str, default="data/classes.json", help="Path to classes.json")
    parser.add_argument("--output", type=str, default="isl_model.keras", help="Path to save trained model")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--arch", type=str, default="bilstm", choices=["bilstm", "cnn_bilstm", "transformer"], help="Model architecture")
    args = parser.parse_args()

    train(args.data, args.classes, output_model=args.output, epochs=args.epochs, batch_size=args.batch_size, arch=args.arch)
