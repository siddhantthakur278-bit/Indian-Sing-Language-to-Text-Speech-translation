"""
ISL Neural Network Architectures Library
Provides three model architectures per Section 10 of the Project Guide:
1. Baseline BiLSTM: Fast training, low latency (~15MB TF.js)
2. Hybrid 1D-CNN + BiLSTM: Extracts short-term finger transitions and long-term trajectory
3. Lightweight Transformer Encoder: Self-attention over 30-frame sequence
"""

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"


def get_model(arch: str = "bilstm", seq_len: int = 30, feat_dim: int = 258, num_classes: int = 70):
    """Factory function returning the compiled Keras model."""
    import tensorflow as tf
    from tensorflow.keras import layers, models

    arch = arch.lower().strip()

    if arch == "bilstm":
        inputs = layers.Input(shape=(seq_len, feat_dim), name="seq_input")
        x = layers.Masking(mask_value=0.0)(inputs)
        x = layers.Bidirectional(layers.LSTM(128, return_sequences=True))(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Bidirectional(layers.LSTM(64))(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Dense(128, activation="relu")(x)
        x = layers.BatchNormalization()(x)
        outputs = layers.Dense(num_classes, activation="softmax")(x)
        model = models.Model(inputs=inputs, outputs=outputs, name="ISL_BiLSTM")

    elif arch == "cnn_bilstm":
        inputs = layers.Input(shape=(seq_len, feat_dim), name="seq_input")
        x = layers.Masking(mask_value=0.0)(inputs)
        # 1D Temporal Convolutions to detect rapid finger motions
        x = layers.Conv1D(filters=64, kernel_size=3, padding="same", activation="relu")(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling1D(pool_size=1)(x)
        x = layers.Conv1D(filters=128, kernel_size=3, padding="same", activation="relu")(x)
        x = layers.BatchNormalization()(x)
        # BiLSTM for global gesture transition
        x = layers.Bidirectional(layers.LSTM(128, return_sequences=True))(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Bidirectional(layers.LSTM(64))(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Dense(128, activation="relu")(x)
        outputs = layers.Dense(num_classes, activation="softmax")(x)
        model = models.Model(inputs=inputs, outputs=outputs, name="ISL_CNN_BiLSTM")

    elif arch == "transformer":
        inputs = layers.Input(shape=(seq_len, feat_dim), name="seq_input")
        # Dense projection to d_model
        x = layers.Dense(128, activation="relu")(inputs)
        # Multi-Head Attention
        attn = layers.MultiHeadAttention(num_heads=4, key_dim=32)(x, x)
        x = layers.Add()([x, attn])
        x = layers.LayerNormalization()(x)
        # Feed-forward sublayer
        ffn = layers.Dense(256, activation="relu")(x)
        ffn = layers.Dense(128)(ffn)
        x = layers.Add()([x, ffn])
        x = layers.LayerNormalization()(x)
        # Global average pool over sequence
        x = layers.GlobalAveragePooling1D()(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Dense(128, activation="relu")(x)
        outputs = layers.Dense(num_classes, activation="softmax")(x)
        model = models.Model(inputs=inputs, outputs=outputs, name="ISL_Transformer")

    else:
        raise ValueError(f"Unknown architecture '{arch}'. Choose from ['bilstm', 'cnn_bilstm', 'transformer']")

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    return model
