"""
ISL Neural Network Architectures Library
========================================
Provides modular deep learning model architectures conforming to
AGENTS.md (Section 8.1) and AGENTS_PARTH_ML.md (Section 7.4 & 7.5):
1. Baseline BiLSTM: Fast training, low latency (~15MB TF.js)
2. Hybrid 1D-CNN + BiLSTM: Extracts short-term finger transitions and long-term trajectory
3. Lightweight Transformer Encoder: Self-attention over 30-frame sequence
"""

import os
from typing import Optional

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"


class ModelFactory:
    """Factory class to construct and compile ISL gesture recognition neural networks."""

    SUPPORTED_ARCHITECTURES = ("bilstm", "cnn_bilstm", "transformer")

    @classmethod
    def create_model(
        cls,
        arch: str = "bilstm",
        seq_len: int = 30,
        feat_dim: int = 258,
        num_classes: int = 70,
        learning_rate: float = 1e-3,
        label_smoothing: float = 0.05,
    ):
        """Constructs and compiles the specified neural network architecture."""
        import tensorflow as tf
        from tensorflow.keras import layers, models, optimizers, losses

        arch_norm = arch.lower().strip()
        if arch_norm not in cls.SUPPORTED_ARCHITECTURES:
            raise ValueError(f"Unknown architecture '{arch}'. Supported: {cls.SUPPORTED_ARCHITECTURES}")

        if arch_norm == "bilstm":
            inputs = layers.Input(shape=(seq_len, feat_dim), name="seq_input")
            x = layers.Masking(mask_value=0.0)(inputs)
            x = layers.Bidirectional(layers.LSTM(128, return_sequences=True))(x)
            x = layers.Dropout(0.3)(x)
            x = layers.Bidirectional(layers.LSTM(64))(x)
            x = layers.Dropout(0.3)(x)
            x = layers.Dense(128, activation="relu")(x)
            x = layers.BatchNormalization()(x)
            outputs = layers.Dense(num_classes, activation="softmax", name="gloss_output")(x)
            model = models.Model(inputs=inputs, outputs=outputs, name="ISL_BiLSTM")

        elif arch_norm == "cnn_bilstm":
            inputs = layers.Input(shape=(seq_len, feat_dim), name="seq_input")
            x = layers.Masking(mask_value=0.0)(inputs)
            # 1D Temporal Convolutions to detect rapid finger transitions
            x = layers.Conv1D(filters=64, kernel_size=3, padding="same", activation="relu")(x)
            x = layers.BatchNormalization()(x)
            x = layers.Conv1D(filters=128, kernel_size=3, padding="same", activation="relu")(x)
            x = layers.BatchNormalization()(x)
            # BiLSTM for temporal trajectory context
            x = layers.Bidirectional(layers.LSTM(128, return_sequences=True))(x)
            x = layers.Dropout(0.3)(x)
            x = layers.Bidirectional(layers.LSTM(64))(x)
            x = layers.Dropout(0.3)(x)
            x = layers.Dense(128, activation="relu")(x)
            outputs = layers.Dense(num_classes, activation="softmax", name="gloss_output")(x)
            model = models.Model(inputs=inputs, outputs=outputs, name="ISL_CNN_BiLSTM")

        elif arch_norm == "transformer":
            inputs = layers.Input(shape=(seq_len, feat_dim), name="seq_input")
            # Linear projection to embedding dimension
            x = layers.Dense(128, activation="relu")(inputs)
            # Multi-Head Attention block
            attn = layers.MultiHeadAttention(num_heads=4, key_dim=32)(x, x)
            x = layers.Add()([x, attn])
            x = layers.LayerNormalization()(x)
            # Feed-forward block
            ffn = layers.Dense(256, activation="relu")(x)
            ffn = layers.Dense(128)(ffn)
            x = layers.Add()([x, ffn])
            x = layers.LayerNormalization()(x)
            # Global pooling
            x = layers.GlobalAveragePooling1D()(x)
            x = layers.Dropout(0.3)(x)
            x = layers.Dense(128, activation="relu")(x)
            outputs = layers.Dense(num_classes, activation="softmax", name="gloss_output")(x)
            model = models.Model(inputs=inputs, outputs=outputs, name="ISL_Transformer")

        optimizer = optimizers.Adam(learning_rate=learning_rate)
        loss_fn = losses.CategoricalCrossentropy(label_smoothing=label_smoothing)

        model.compile(
            optimizer=optimizer,
            loss=loss_fn,
            metrics=["accuracy", tf.keras.metrics.TopKCategoricalAccuracy(k=5, name="top_5_acc")],
        )
        return model


def get_model(arch: str = "bilstm", seq_len: int = 30, feat_dim: int = 258, num_classes: int = 70):
    """Backward-compatible functional API wrapping ModelFactory."""
    return ModelFactory.create_model(arch=arch, seq_len=seq_len, feat_dim=feat_dim, num_classes=num_classes)


def validate_model_checkpoint(
    model_path: str,
    expected_seq_len: int = 30,
    expected_feat_dim: int = 258,
    expected_num_classes: Optional[int] = 70,
) -> dict:
    """
    Validates a saved model checkpoint file:
    1. Checks file existence and non-zero size.
    2. Safely loads the model if TensorFlow is available.
    3. Validates input tensor shape: (None, expected_seq_len, expected_feat_dim).
    4. Validates output tensor shape: (None, expected_num_classes).
    Returns dict with validity, shapes, parameter counts, and diagnostics.
    """
    if not os.path.exists(model_path):
        return {"valid": False, "error": f"Model file '{model_path}' does not exist"}

    file_size_bytes = os.path.getsize(model_path)
    if file_size_bytes == 0:
        return {"valid": False, "error": f"Model file '{model_path}' is empty (0 bytes)"}

    try:
        import tensorflow as tf
    except ImportError:
        return {
            "valid": True,
            "file_size_bytes": file_size_bytes,
            "file_size_mb": file_size_bytes / (1024 * 1024),
            "warning": "TensorFlow not installed in current environment; file presence verified",
        }

    try:
        model = tf.keras.models.load_model(model_path)
    except Exception as e:
        return {"valid": False, "error": f"Failed to deserialize model checkpoint: {e}"}

    input_shape = getattr(model, "input_shape", None)
    output_shape = getattr(model, "output_shape", None)

    expected_in = (None, expected_seq_len, expected_feat_dim)
    if input_shape != expected_in:
        return {
            "valid": False,
            "error": f"Input shape mismatch: expected {expected_in}, got {input_shape}",
            "input_shape": input_shape,
            "output_shape": output_shape,
        }

    if expected_num_classes is not None:
        expected_out = (None, expected_num_classes)
        if output_shape != expected_out:
            return {
                "valid": False,
                "error": f"Output shape mismatch: expected {expected_out}, got {output_shape}",
                "input_shape": input_shape,
                "output_shape": output_shape,
            }

    return {
        "valid": True,
        "input_shape": input_shape,
        "output_shape": output_shape,
        "num_classes": output_shape[-1] if output_shape else None,
        "file_size_mb": file_size_bytes / (1024 * 1024),
        "total_params": model.count_params() if hasattr(model, "count_params") else None,
        "error": None,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ISL Model Architecture & Checkpoint Validator")
    parser.add_argument("--validate-checkpoint", type=str, help="Path to .keras model checkpoint to inspect")
    parser.add_argument("--seq_len", type=int, default=30, help="Expected sequence length (default: 30)")
    parser.add_argument("--feat_dim", type=int, default=258, help="Expected feature dimension (default: 258)")
    parser.add_argument("--classes", type=int, default=70, help="Expected number of classes (default: 70)")
    args = parser.parse_args()

    if args.validate_checkpoint:
        result = validate_model_checkpoint(
            args.validate_checkpoint,
            expected_seq_len=args.seq_len,
            expected_feat_dim=args.feat_dim,
            expected_num_classes=args.classes,
        )
        print("Checkpoint Validation Result:")
        for k, v in result.items():
            print(f"  {k}: {v}")
    else:
        parser.print_help()
