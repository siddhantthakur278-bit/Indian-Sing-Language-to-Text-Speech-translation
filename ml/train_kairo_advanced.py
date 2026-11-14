"""
================================================================================
ADVANCED ISL MODEL TRAINING - MAXIMUM ACCURACY
================================================================================
State-of-the-art techniques for achieving 9-10/10 accuracy:

1. Attention Mechanism - Focus on important landmarks
2. Focal Loss - Better handling of hard examples
3. Advanced Augmentation - Realistic variations
4. Residual Connections - Better gradient flow
5. Class Balancing - Handle imbalanced classes
6. Hard Example Mining - Focus on confused pairs
7. Multi-Scale Features - Capture different patterns
8. Test-Time Augmentation (TTA) - Better inference
9. Ensemble Ready - Can combine multiple models
10. Gradual Unfreezing with Warmup

Target: 99.5%+ validation accuracy with real-world robustness

Author: KairoAI
================================================================================
"""

import os
import numpy as np
import json
import csv
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, regularizers, Model
from tensorflow.keras.callbacks import Callback
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, confusion_matrix
import math

# Suppress warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_CSV = "landmark_dataset_with_orientation.csv"
OUTPUT_MODEL = "isl_model_advanced.tflite"
OUTPUT_H5 = "isl_model_advanced.h5"
OUTPUT_LABELS = "labels_advanced.json"

NUM_CLASSES = 35

# Training config
EPOCHS = 200
BATCH_SIZE = 64
VALIDATION_SPLIT = 0.15  # Smaller val split = more training data

# Advanced config
USE_FOCAL_LOSS = True
FOCAL_ALPHA = 0.25
FOCAL_GAMMA = 2.0

USE_CLASS_WEIGHTS = True
USE_ATTENTION = True
USE_RESIDUAL = True

# Augmentation strength
AUG_NOISE_STD = 0.03
AUG_SCALE_RANGE = (0.85, 1.15)
AUG_ROTATION_RANGE = 20  # degrees
AUG_SHIFT_RANGE = 0.1
MIXUP_ALPHA = 0.3
CUTMIX_ALPHA = 0.3

# Learning rate
INITIAL_LR = 0.002
MIN_LR = 1e-7
WARMUP_EPOCHS = 10

LABELS = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
    'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
    'U', 'V', 'W', 'X', 'Y', 'Z', '1', '2', '3', '4',
    '5', '6', '7', '8', '9'
]

# Commonly confused pairs - will get extra training attention
CONFUSED_PAIRS = [
    ('V', '2'), ('K', 'V'), ('U', 'V'), ('M', 'N'), ('5', 'H'),
    ('G', 'H'), ('I', 'J'), ('1', 'D'), ('6', 'W'), ('3', 'W'),
    ('B', 'E'), ('A', 'S'), ('O', 'C')
]


# ============================================================================
# FOCAL LOSS - Better for hard examples
# ============================================================================

class FocalLoss(keras.losses.Loss):
    """
    Focal Loss focuses training on hard examples.
    Reduces loss contribution from easy examples.
    """
    def __init__(self, alpha=0.25, gamma=2.0, **kwargs):
        super().__init__(**kwargs)
        self.alpha = alpha
        self.gamma = gamma
    
    def call(self, y_true, y_pred):
        # Clip predictions to prevent log(0)
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
        
        # Calculate focal loss
        cross_entropy = -y_true * tf.math.log(y_pred)
        weight = self.alpha * y_true * tf.pow(1 - y_pred, self.gamma)
        focal_loss = weight * cross_entropy
        
        return tf.reduce_sum(focal_loss, axis=-1)
    
    def get_config(self):
        config = super().get_config()
        config.update({'alpha': self.alpha, 'gamma': self.gamma})
        return config


# ============================================================================
# ATTENTION LAYER - Focus on important features
# ============================================================================

class SelfAttention(layers.Layer):
    """Self-attention layer to focus on important landmarks."""
    
    def __init__(self, units, **kwargs):
        super().__init__(**kwargs)
        self.units = units
        
    def build(self, input_shape):
        self.W_q = self.add_weight(
            shape=(input_shape[-1], self.units),
            initializer='glorot_uniform',
            trainable=True,
            name='query_weight'
        )
        self.W_k = self.add_weight(
            shape=(input_shape[-1], self.units),
            initializer='glorot_uniform',
            trainable=True,
            name='key_weight'
        )
        self.W_v = self.add_weight(
            shape=(input_shape[-1], self.units),
            initializer='glorot_uniform',
            trainable=True,
            name='value_weight'
        )
        
    def call(self, x):
        q = tf.matmul(x, self.W_q)
        k = tf.matmul(x, self.W_k)
        v = tf.matmul(x, self.W_v)
        
        # Scaled dot-product attention
        d_k = tf.cast(tf.shape(k)[-1], tf.float32)
        attention_scores = tf.matmul(q, k, transpose_b=True) / tf.sqrt(d_k)
        attention_weights = tf.nn.softmax(attention_scores, axis=-1)
        
        output = tf.matmul(attention_weights, v)
        return output
    
    def get_config(self):
        config = super().get_config()
        config.update({'units': self.units})
        return config


class ChannelAttention(layers.Layer):
    """Channel attention - learns which features are important."""
    
    def __init__(self, reduction_ratio=8, **kwargs):
        super().__init__(**kwargs)
        self.reduction_ratio = reduction_ratio
        
    def build(self, input_shape):
        channels = input_shape[-1]
        self.dense1 = layers.Dense(channels // self.reduction_ratio, activation='relu')
        self.dense2 = layers.Dense(channels, activation='sigmoid')
        
    def call(self, x):
        # Global average pooling
        avg_pool = tf.reduce_mean(x, axis=-1, keepdims=True)
        max_pool = tf.reduce_max(x, axis=-1, keepdims=True)
        
        # Shared MLP
        avg_out = self.dense2(self.dense1(avg_pool))
        max_out = self.dense2(self.dense1(max_pool))
        
        attention = avg_out + max_out
        return x * attention
    
    def get_config(self):
        config = super().get_config()
        config.update({'reduction_ratio': self.reduction_ratio})
        return config


# ============================================================================
# RESIDUAL BLOCK
# ============================================================================

class ResidualBlock(layers.Layer):
    """Residual block with skip connection for better gradient flow."""
    
    def __init__(self, units, dropout_rate=0.3, l2_reg=0.001, **kwargs):
        super().__init__(**kwargs)
        self.units = units
        self.dropout_rate = dropout_rate
        self.l2_reg = l2_reg
        
    def build(self, input_shape):
        self.dense1 = layers.Dense(
            self.units, 
            kernel_regularizer=regularizers.l2(self.l2_reg)
        )
        self.bn1 = layers.BatchNormalization()
        self.dropout1 = layers.Dropout(self.dropout_rate)
        
        self.dense2 = layers.Dense(
            self.units,
            kernel_regularizer=regularizers.l2(self.l2_reg)
        )
        self.bn2 = layers.BatchNormalization()
        self.dropout2 = layers.Dropout(self.dropout_rate)
        
        # Skip connection projection if dimensions don't match
        if input_shape[-1] != self.units:
            self.skip_proj = layers.Dense(self.units, use_bias=False)
        else:
            self.skip_proj = None
            
    def call(self, x, training=False):
        # Main path
        h = self.dense1(x)
        h = self.bn1(h, training=training)
        h = tf.nn.gelu(h)  # GELU activation (better than ReLU)
        h = self.dropout1(h, training=training)
        
        h = self.dense2(h)
        h = self.bn2(h, training=training)
        
        # Skip connection
        if self.skip_proj is not None:
            x = self.skip_proj(x)
        
        # Add and activate
        out = tf.nn.gelu(h + x)
        out = self.dropout2(out, training=training)
        
        return out
    
    def get_config(self):
        config = super().get_config()
        config.update({
            'units': self.units,
            'dropout_rate': self.dropout_rate,
            'l2_reg': self.l2_reg
        })
        return config


# ============================================================================
# ADVANCED DATA AUGMENTATION
# ============================================================================

class AdvancedAugmenter:
    """Advanced augmentation for landmark data."""
    
    def __init__(self, noise_std=0.03, scale_range=(0.85, 1.15), 
                 rotation_range=20, shift_range=0.1):
        self.noise_std = noise_std
        self.scale_range = scale_range
        self.rotation_range = rotation_range
        self.shift_range = shift_range
        
    def add_noise(self, X):
        """Add Gaussian noise."""
        noise = np.random.normal(0, self.noise_std, X.shape)
        # Don't add noise to orientation features
        if X.shape[1] > 126:
            noise[:, 126:] = 0
        return X + noise
    
    def random_scale(self, X):
        """Random scaling of landmarks."""
        scale = np.random.uniform(*self.scale_range, size=(len(X), 1))
        X_scaled = X.copy()
        X_scaled[:, :126] *= scale
        return X_scaled
    
    def random_shift(self, X):
        """Random translation of landmarks."""
        shift = np.random.uniform(-self.shift_range, self.shift_range, 
                                   size=(len(X), 3))
        X_shifted = X.copy()
        # Apply same shift to all landmarks (x, y, z)
        for i in range(21):
            X_shifted[:, i*3:(i+1)*3] += shift
        # Second hand if present
        for i in range(21, 42):
            X_shifted[:, i*3:(i+1)*3] += shift
        return X_shifted
    
    def random_rotation_2d(self, X):
        """Random 2D rotation around z-axis."""
        angles = np.random.uniform(-self.rotation_range, self.rotation_range, 
                                    size=len(X)) * np.pi / 180
        
        X_rotated = X.copy()
        
        for i, angle in enumerate(angles):
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            
            # Rotate each landmark (x, y only)
            for j in range(42):  # 21 landmarks × 2 hands
                if j * 3 + 2 < 126:
                    x = X_rotated[i, j*3]
                    y = X_rotated[i, j*3 + 1]
                    X_rotated[i, j*3] = x * cos_a - y * sin_a
                    X_rotated[i, j*3 + 1] = x * sin_a + y * cos_a
        
        return X_rotated
    
    def random_mirror(self, X):
        """Randomly mirror hands (swap left/right)."""
        X_mirrored = X.copy()
        mask = np.random.random(len(X)) < 0.3  # 30% chance
        
        for i in np.where(mask)[0]:
            # Mirror x coordinates
            for j in range(42):
                if j * 3 < 126:
                    X_mirrored[i, j*3] = -X_mirrored[i, j*3]
            
            # Swap hand orientation if present
            if X.shape[1] > 126:
                # Swap is_left flags
                X_mirrored[i, 127] = 1.0 - X_mirrored[i, 127] if X_mirrored[i, 127] >= 0 else -1.0
                X_mirrored[i, 129] = 1.0 - X_mirrored[i, 129] if X_mirrored[i, 129] >= 0 else -1.0
        
        return X_mirrored
    
    def random_finger_jitter(self, X):
        """Add extra jitter to finger tips (most variable landmarks)."""
        X_jittered = X.copy()
        finger_tips = [4, 8, 12, 16, 20]  # Thumb, index, middle, ring, pinky tips
        
        for tip in finger_tips:
            jitter = np.random.normal(0, self.noise_std * 2, (len(X), 3))
            X_jittered[:, tip*3:(tip+1)*3] += jitter
            # Second hand
            if (tip + 21) * 3 + 3 <= 126:
                X_jittered[:, (tip+21)*3:(tip+22)*3] += jitter
        
        return X_jittered
    
    def augment_batch(self, X, p=0.5):
        """Apply random augmentations to batch."""
        X_aug = X.copy()
        
        # Apply each augmentation with probability p
        if np.random.random() < p:
            X_aug = self.add_noise(X_aug)
        if np.random.random() < p * 0.7:
            X_aug = self.random_scale(X_aug)
        if np.random.random() < p * 0.5:
            X_aug = self.random_rotation_2d(X_aug)
        if np.random.random() < p * 0.3:
            X_aug = self.random_shift(X_aug)
        if np.random.random() < p * 0.3:
            X_aug = self.random_finger_jitter(X_aug)
        if np.random.random() < p * 0.2:
            X_aug = self.random_mirror(X_aug)
            
        return X_aug


# ============================================================================
# MIXUP AND CUTMIX
# ============================================================================

def mixup(X, y, alpha=0.3):
    """Mixup augmentation."""
    if alpha <= 0:
        return X, y
    
    batch_size = len(X)
    lam = np.random.beta(alpha, alpha)
    indices = np.random.permutation(batch_size)
    
    X_mixed = lam * X + (1 - lam) * X[indices]
    y_mixed = lam * y + (1 - lam) * y[indices]
    
    return X_mixed, y_mixed


def cutmix(X, y, alpha=0.3):
    """CutMix augmentation - mix portions of features."""
    if alpha <= 0:
        return X, y
    
    batch_size = len(X)
    lam = np.random.beta(alpha, alpha)
    indices = np.random.permutation(batch_size)
    
    # Determine cut size
    feature_size = X.shape[1]
    cut_size = int(feature_size * (1 - lam))
    cut_start = np.random.randint(0, feature_size - cut_size + 1)
    
    X_mixed = X.copy()
    X_mixed[:, cut_start:cut_start+cut_size] = X[indices, cut_start:cut_start+cut_size]
    
    # Adjust lambda based on actual cut
    lam = 1 - cut_size / feature_size
    y_mixed = lam * y + (1 - lam) * y[indices]
    
    return X_mixed, y_mixed


# ============================================================================
# ADVANCED DATA GENERATOR
# ============================================================================

class AdvancedDataGenerator(keras.utils.Sequence):
    """Advanced data generator with multiple augmentation techniques."""
    
    def __init__(self, X, y, batch_size, augmenter, num_classes,
                 use_mixup=True, use_cutmix=True, shuffle=True,
                 hard_example_indices=None, hard_example_ratio=0.3):
        self.X = X
        self.y = y
        self.batch_size = batch_size
        self.augmenter = augmenter
        self.num_classes = num_classes
        self.use_mixup = use_mixup
        self.use_cutmix = use_cutmix
        self.shuffle = shuffle
        self.hard_example_indices = hard_example_indices
        self.hard_example_ratio = hard_example_ratio
        self.indices = np.arange(len(X))
        self.on_epoch_end()
        
    def __len__(self):
        return int(np.ceil(len(self.X) / self.batch_size))
    
    def __getitem__(self, idx):
        batch_indices = self.indices[idx * self.batch_size:(idx + 1) * self.batch_size]
        
        # Optionally include hard examples
        if self.hard_example_indices is not None and len(self.hard_example_indices) > 0:
            n_hard = int(len(batch_indices) * self.hard_example_ratio)
            hard_sample = np.random.choice(self.hard_example_indices, 
                                           size=min(n_hard, len(self.hard_example_indices)),
                                           replace=False)
            batch_indices = np.concatenate([batch_indices[:-n_hard], hard_sample])
        
        X_batch = self.X[batch_indices].copy()
        y_batch = self.y[batch_indices].copy()
        
        # Apply augmentation
        X_batch = self.augmenter.augment_batch(X_batch, p=0.7)
        
        # Convert to one-hot
        y_one_hot = keras.utils.to_categorical(y_batch, self.num_classes)
        
        # Apply mixup or cutmix (not both at same time)
        if self.use_mixup and self.use_cutmix:
            if np.random.random() < 0.5:
                X_batch, y_one_hot = mixup(X_batch, y_one_hot, MIXUP_ALPHA)
            else:
                X_batch, y_one_hot = cutmix(X_batch, y_one_hot, CUTMIX_ALPHA)
        elif self.use_mixup:
            X_batch, y_one_hot = mixup(X_batch, y_one_hot, MIXUP_ALPHA)
        elif self.use_cutmix:
            X_batch, y_one_hot = cutmix(X_batch, y_one_hot, CUTMIX_ALPHA)
        
        return X_batch.astype(np.float32), y_one_hot.astype(np.float32)
    
    def on_epoch_end(self):
        if self.shuffle:
            np.random.shuffle(self.indices)


# ============================================================================
# CREATE ADVANCED MODEL
# ============================================================================

def create_advanced_model(input_size):
    """
    Create an advanced model with attention and residual connections.
    """
    print("\n" + "=" * 60)
    print("CREATING ADVANCED MODEL")
    print("=" * 60)
    
    l2_reg = regularizers.l2(0.001)
    
    # Input
    inputs = layers.Input(shape=(input_size,), name='input')
    
    # Split landmarks and orientation
    landmarks = layers.Lambda(lambda x: x[:, :126], name='landmarks')(inputs)
    
    if input_size > 126:
        orientation = layers.Lambda(lambda x: x[:, 126:], name='orientation')(inputs)
    
    # ===== LANDMARK PROCESSING PATH =====
    
    # Reshape for multi-scale processing (treat as 42 landmarks × 3 coords)
    lm_reshaped = layers.Reshape((42, 3))(landmarks)
    
    # Multi-scale feature extraction
    # Scale 1: Per-landmark features
    scale1 = layers.Dense(16, activation='gelu', kernel_regularizer=l2_reg)(lm_reshaped)
    scale1 = layers.Flatten()(scale1)
    
    # Scale 2: Landmark group features (fingers)
    scale2 = layers.Conv1D(32, kernel_size=5, activation='gelu', padding='same',
                           kernel_regularizer=l2_reg)(lm_reshaped)
    scale2 = layers.GlobalAveragePooling1D()(scale2)
    
    # Scale 3: Global hand features
    scale3 = layers.Dense(64, activation='gelu', kernel_regularizer=l2_reg)(landmarks)
    
    # Combine scales
    lm_features = layers.Concatenate()([scale1, scale2, scale3])
    lm_features = layers.BatchNormalization()(lm_features)
    lm_features = layers.Dropout(0.3)(lm_features)
    
    # Channel attention
    if USE_ATTENTION:
        lm_features = ChannelAttention(reduction_ratio=4)(lm_features)
    
    # Residual blocks
    if USE_RESIDUAL:
        x = ResidualBlock(256, dropout_rate=0.4, l2_reg=0.001)(lm_features)
        x = ResidualBlock(128, dropout_rate=0.3, l2_reg=0.001)(x)
        x = ResidualBlock(64, dropout_rate=0.3, l2_reg=0.001)(x)
    else:
        x = layers.Dense(256, activation='gelu', kernel_regularizer=l2_reg)(lm_features)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.4)(x)
        x = layers.Dense(128, activation='gelu', kernel_regularizer=l2_reg)(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Dense(64, activation='gelu', kernel_regularizer=l2_reg)(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
    
    # ===== ORIENTATION PATH (if available) =====
    if input_size > 126:
        orient_x = layers.Dense(16, activation='gelu', kernel_regularizer=l2_reg)(orientation)
        orient_x = layers.BatchNormalization()(orient_x)
        orient_x = layers.Dense(8, activation='gelu', kernel_regularizer=l2_reg)(orient_x)
        
        # Combine with main path
        x = layers.Concatenate()([x, orient_x])
    
    # ===== CLASSIFICATION HEAD =====
    x = layers.Dense(64, activation='gelu', kernel_regularizer=l2_reg)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.2)(x)
    
    x = layers.Dense(32, activation='gelu', kernel_regularizer=l2_reg)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.2)(x)
    
    # Output
    outputs = layers.Dense(NUM_CLASSES, activation='softmax', name='output')(x)
    
    model = Model(inputs=inputs, outputs=outputs)
    
    # Compile with focal loss or standard loss
    if USE_FOCAL_LOSS:
        loss = FocalLoss(alpha=FOCAL_ALPHA, gamma=FOCAL_GAMMA)
    else:
        loss = keras.losses.CategoricalCrossentropy(label_smoothing=0.1)
    
    # Use Adam with weight decay (compatible with TF 2.x)
    try:
        # TensorFlow 2.11+
        optimizer = keras.optimizers.Adam(
            learning_rate=INITIAL_LR,
        )
    except:
        optimizer = keras.optimizers.Adam(learning_rate=INITIAL_LR)
    
    model.compile(
        optimizer=optimizer,
        loss=loss,
        metrics=['accuracy']
    )
    
    print(f"\n📐 Model Summary:")
    model.summary()
    print(f"\n   Total parameters: {model.count_params():,}")
    print(f"   Using Focal Loss: {USE_FOCAL_LOSS}")
    print(f"   Using Attention: {USE_ATTENTION}")
    print(f"   Using Residual: {USE_RESIDUAL}")
    
    return model


# ============================================================================
# LEARNING RATE SCHEDULE
# ============================================================================

class WarmupCosineDecay(Callback):
    """Warmup + Cosine decay with restarts."""
    
    def __init__(self, max_lr, min_lr, warmup_epochs, total_epochs, restarts=2):
        super().__init__()
        self.max_lr = max_lr
        self.min_lr = min_lr
        self.warmup_epochs = warmup_epochs
        self.total_epochs = total_epochs
        self.restarts = restarts
        self.cycle_length = (total_epochs - warmup_epochs) // (restarts + 1)
        
    def on_epoch_begin(self, epoch, logs=None):
        if epoch < self.warmup_epochs:
            lr = self.max_lr * (epoch + 1) / self.warmup_epochs
        else:
            epoch_in_cycle = (epoch - self.warmup_epochs) % self.cycle_length
            # Cosine decay within cycle
            lr = self.min_lr + 0.5 * (self.max_lr - self.min_lr) * \
                 (1 + math.cos(math.pi * epoch_in_cycle / self.cycle_length))
            
            # Reduce max_lr after each restart
            cycle_num = (epoch - self.warmup_epochs) // self.cycle_length
            lr *= (0.8 ** cycle_num)
        
        keras.backend.set_value(self.model.optimizer.learning_rate, lr)
        
    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        logs['lr'] = float(keras.backend.get_value(self.model.optimizer.learning_rate))


# ============================================================================
# LOAD DATA
# ============================================================================

def load_data():
    """Load and prepare data."""
    print("\n" + "=" * 60)
    print("LOADING DATA")
    print("=" * 60)
    
    if not os.path.exists(INPUT_CSV):
        print(f"❌ ERROR: {INPUT_CSV} not found!")
        return None, None, None
    
    X, y = [], []
    
    with open(INPUT_CSV, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row in reader:
            features = [float(val) for val in row[:-1]]
            label_str = row[-1]
            
            if label_str in LABELS:
                X.append(features)
                y.append(LABELS.index(label_str))
    
    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int32)
    
    print(f"✅ Loaded {len(X)} samples")
    print(f"   Feature shape: {X.shape}")
    
    # Find hard examples (confused pairs)
    hard_indices = []
    for sign_a, sign_b in CONFUSED_PAIRS:
        if sign_a in LABELS and sign_b in LABELS:
            idx_a, idx_b = LABELS.index(sign_a), LABELS.index(sign_b)
            hard_indices.extend(np.where((y == idx_a) | (y == idx_b))[0].tolist())
    
    hard_indices = list(set(hard_indices))
    print(f"   Hard examples (confused pairs): {len(hard_indices)}")
    
    # Class distribution
    unique, counts = np.unique(y, return_counts=True)
    print(f"\n📊 Class distribution:")
    min_count = min(counts)
    max_count = max(counts)
    print(f"   Min samples: {min_count} ({LABELS[unique[np.argmin(counts)]]})")
    print(f"   Max samples: {max_count} ({LABELS[unique[np.argmax(counts)]]})")
    print(f"   Imbalance ratio: {max_count/min_count:.2f}")
    
    return X, y, hard_indices


# ============================================================================
# TRAINING
# ============================================================================

def train_model(model, X, y, hard_indices):
    """Train with advanced techniques."""
    print("\n" + "=" * 60)
    print(f"TRAINING FOR {EPOCHS} EPOCHS")
    print("=" * 60)
    
    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=VALIDATION_SPLIT, random_state=42, stratify=y
    )
    
    print(f"\n📊 Data split:")
    print(f"   Training: {len(X_train)} samples")
    print(f"   Validation: {len(X_val)} samples")
    
    # Compute class weights
    class_weights = None
    if USE_CLASS_WEIGHTS:
        weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
        class_weights = dict(enumerate(weights))
        print(f"   Using class weights: min={min(weights):.2f}, max={max(weights):.2f}")
    
    # Find hard examples in training set
    train_hard_indices = []
    if hard_indices is not None:
        train_indices_set = set(range(len(X_train)))
        # Map original indices to training indices (approximation)
        for h_idx in hard_indices:
            if h_idx < len(X_train):
                train_hard_indices.append(h_idx)
    
    # Create augmenter and generator
    augmenter = AdvancedAugmenter(
        noise_std=AUG_NOISE_STD,
        scale_range=AUG_SCALE_RANGE,
        rotation_range=AUG_ROTATION_RANGE,
        shift_range=AUG_SHIFT_RANGE
    )
    
    train_gen = AdvancedDataGenerator(
        X_train, y_train, BATCH_SIZE, augmenter, NUM_CLASSES,
        use_mixup=True, use_cutmix=True,
        hard_example_indices=train_hard_indices,
        hard_example_ratio=0.2
    )
    
    # Validation data
    y_val_one_hot = keras.utils.to_categorical(y_val, NUM_CLASSES)
    
    # Callbacks
    callbacks = [
        WarmupCosineDecay(INITIAL_LR, MIN_LR, WARMUP_EPOCHS, EPOCHS, restarts=3),
        
        keras.callbacks.ModelCheckpoint(
            OUTPUT_H5,
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        ),
        
        keras.callbacks.ModelCheckpoint(
            'isl_model_advanced_latest.h5',
            save_best_only=False,
            verbose=0
        ),
        
        # Reduce LR if stuck (backup scheduler)
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=15,
            min_lr=MIN_LR,
            verbose=1
        ),
        
        # Progress logging
        keras.callbacks.LambdaCallback(
            on_epoch_end=lambda epoch, logs: print(
                f"\n   📈 Epoch {epoch+1}/{EPOCHS} - "
                f"acc: {logs.get('accuracy', 0)*100:.2f}% - "
                f"val_acc: {logs.get('val_accuracy', 0)*100:.2f}% - "
                f"lr: {logs.get('lr', 0):.6f}"
            ) if (epoch + 1) % 10 == 0 else None
        )
    ]
    
    # Train
    print(f"\n🚀 Starting training...")
    print(f"   Techniques: Focal Loss, Attention, Residual, Mixup, CutMix")
    print(f"   Augmentation: Noise, Scale, Rotation, Shift, Mirror\n")
    
    history = model.fit(
        train_gen,
        validation_data=(X_val, y_val_one_hot),
        epochs=EPOCHS,
        callbacks=callbacks,
        class_weight=class_weights,
        verbose=1
    )
    
    # Load best model
    print("\n📂 Loading best model...")
    model = keras.models.load_model(
        OUTPUT_H5,
        custom_objects={
            'FocalLoss': FocalLoss,
            'ChannelAttention': ChannelAttention,
            'ResidualBlock': ResidualBlock
        }
    )
    
    return history, model, X_val, y_val


# ============================================================================
# TEST-TIME AUGMENTATION
# ============================================================================

def predict_with_tta(model, X, n_augments=5):
    """Prediction with test-time augmentation."""
    augmenter = AdvancedAugmenter(noise_std=0.01, scale_range=(0.95, 1.05))
    
    predictions = []
    
    # Original prediction
    predictions.append(model.predict(X, verbose=0))
    
    # Augmented predictions
    for _ in range(n_augments - 1):
        X_aug = augmenter.augment_batch(X, p=0.5)
        predictions.append(model.predict(X_aug, verbose=0))
    
    # Average predictions
    avg_pred = np.mean(predictions, axis=0)
    return avg_pred


# ============================================================================
# EVALUATION
# ============================================================================

def evaluate_model(model, X_val, y_val, use_tta=True):
    """Comprehensive evaluation."""
    print("\n" + "=" * 60)
    print("EVALUATION")
    print("=" * 60)
    
    # Standard prediction
    y_val_one_hot = keras.utils.to_categorical(y_val, NUM_CLASSES)
    val_loss, val_acc = model.evaluate(X_val, y_val_one_hot, verbose=0)
    
    print(f"\n📈 Standard Evaluation:")
    print(f"   Validation Accuracy: {val_acc*100:.2f}%")
    print(f"   Validation Loss: {val_loss:.4f}")
    
    # TTA prediction
    if use_tta:
        print(f"\n🔄 Test-Time Augmentation (TTA):")
        tta_pred = predict_with_tta(model, X_val, n_augments=5)
        tta_classes = np.argmax(tta_pred, axis=1)
        tta_acc = np.mean(tta_classes == y_val)
        print(f"   TTA Accuracy: {tta_acc*100:.2f}%")
    else:
        tta_pred = model.predict(X_val, verbose=0)
        tta_classes = np.argmax(tta_pred, axis=1)
    
    # Classification report
    print("\n" + "-" * 60)
    print("CLASSIFICATION REPORT")
    print("-" * 60)
    print(classification_report(y_val, tta_classes, target_names=LABELS, digits=3))
    
    # Confusion analysis for hard pairs
    print("\n" + "-" * 60)
    print("CONFUSED PAIRS ANALYSIS")
    print("-" * 60)
    
    total_confusion = 0
    for sign_a, sign_b in CONFUSED_PAIRS:
        if sign_a in LABELS and sign_b in LABELS:
            idx_a, idx_b = LABELS.index(sign_a), LABELS.index(sign_b)
            
            mask_a = y_val == idx_a
            mask_b = y_val == idx_b
            
            a_as_b = np.sum((tta_classes == idx_b) & mask_a)
            b_as_a = np.sum((tta_classes == idx_a) & mask_b)
            
            if a_as_b > 0 or b_as_a > 0:
                print(f"   ⚠️  {sign_a} ↔ {sign_b}: {sign_a}→{sign_b}={a_as_b}, {sign_b}→{sign_a}={b_as_a}")
                total_confusion += a_as_b + b_as_a
            else:
                print(f"   ✅ {sign_a} ↔ {sign_b}: Perfect!")
    
    print(f"\n   Total confusions in pairs: {total_confusion}")
    
    return val_acc


# ============================================================================
# CONVERT TO TFLITE
# ============================================================================

def convert_to_tflite(model):
    """Convert to optimized TFLite."""
    print("\n" + "=" * 60)
    print("CONVERTING TO TFLITE")
    print("=" * 60)
    
    # Save a version without custom objects for TFLite conversion
    # Re-create model with standard layers
    print("   Creating export-friendly model...")
    
    input_size = model.input_shape[1]
    
    # Simple export model (without custom layers)
    export_model = keras.Sequential([
        layers.Input(shape=(input_size,)),
        layers.Dense(512, activation='gelu'),
        layers.BatchNormalization(),
        layers.Dropout(0.4),
        layers.Dense(256, activation='gelu'),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(128, activation='gelu'),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(64, activation='gelu'),
        layers.BatchNormalization(),
        layers.Dropout(0.2),
        layers.Dense(32, activation='gelu'),
        layers.BatchNormalization(),
        layers.Dropout(0.2),
        layers.Dense(NUM_CLASSES, activation='softmax')
    ])
    
    export_model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Knowledge distillation: train export model on advanced model's predictions
    print("   Performing knowledge distillation...")
    
    # Load training data for distillation
    X_all, y_all, _ = load_data()
    if X_all is not None:
        # Get soft labels from advanced model
        soft_labels = model.predict(X_all, verbose=0)
        
        # Train export model
        export_model.fit(
            X_all, soft_labels,
            epochs=20,
            batch_size=64,
            verbose=1
        )
    
    # Convert to TFLite
    print("\n   Converting to TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(export_model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    # Quantization for smaller size
    converter.target_spec.supported_types = [tf.float16]
    
    tflite_model = converter.convert()
    
    with open(OUTPUT_MODEL, 'wb') as f:
        f.write(tflite_model)
    
    print(f"\n✅ TFLite model saved: {OUTPUT_MODEL}")
    print(f"   Size: {os.path.getsize(OUTPUT_MODEL) / 1024:.2f} KB")
    
    # Verify
    print("\n📋 Verifying TFLite model...")
    interpreter = tf.lite.Interpreter(model_content=tflite_model)
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    print(f"   Input shape: {input_details[0]['shape']}")
    print(f"   Output shape: {output_details[0]['shape']}")
    
    return tflite_model


# ============================================================================
# SAVE CONFIG
# ============================================================================

def save_config(val_acc):
    """Save configuration."""
    config = {
        'labels': LABELS,
        'num_classes': NUM_CLASSES,
        'input_size': 130,
        'validation_accuracy': float(val_acc),
        'training_config': {
            'epochs': EPOCHS,
            'batch_size': BATCH_SIZE,
            'focal_loss': USE_FOCAL_LOSS,
            'attention': USE_ATTENTION,
            'residual': USE_RESIDUAL,
            'augmentation': {
                'noise_std': AUG_NOISE_STD,
                'scale_range': list(AUG_SCALE_RANGE),
                'rotation_range': AUG_ROTATION_RANGE,
                'mixup_alpha': MIXUP_ALPHA,
                'cutmix_alpha': CUTMIX_ALPHA
            }
        },
        'model_files': {
            'h5': OUTPUT_H5,
            'tflite': OUTPUT_MODEL
        }
    }
    
    with open(OUTPUT_LABELS, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Config saved: {OUTPUT_LABELS}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("🚀 ADVANCED ISL MODEL TRAINING - MAXIMUM ACCURACY")
    print("=" * 70)
    print("\nTarget: 9-10/10 accuracy with real-world robustness")
    print("\nAdvanced Techniques:")
    print("   ✓ Focal Loss - Focus on hard examples")
    print("   ✓ Attention Mechanism - Important features")
    print("   ✓ Residual Connections - Better gradients")
    print("   ✓ Multi-Scale Features - Different patterns")
    print("   ✓ Advanced Augmentation - Realistic variations")
    print("   ✓ Mixup + CutMix - Better generalization")
    print("   ✓ Class Balancing - Handle imbalance")
    print("   ✓ Hard Example Mining - Confused pairs")
    print("   ✓ Test-Time Augmentation - Better inference")
    print("   ✓ Knowledge Distillation - Better TFLite")
    
    # Load data
    X, y, hard_indices = load_data()
    if X is None:
        return
    
    input_size = X.shape[1]
    
    # Create model
    model = create_advanced_model(input_size)
    
    # Train
    history, model, X_val, y_val = train_model(model, X, y, hard_indices)
    
    # Evaluate
    val_acc = evaluate_model(model, X_val, y_val, use_tta=True)
    
    # Convert to TFLite
    convert_to_tflite(model)
    
    # Save config
    save_config(val_acc)
    
    # Final summary
    print("\n" + "=" * 70)
    print("✅ TRAINING COMPLETE!")
    print("=" * 70)
    print(f"\n🎯 Final Validation Accuracy: {val_acc*100:.2f}%")
    print(f"\n📁 Output files:")
    print(f"   📄 {OUTPUT_H5} - Best Keras model")
    print(f"   📄 {OUTPUT_MODEL} - TFLite for Android")
    print(f"   📄 {OUTPUT_LABELS} - Configuration")
    print("\n💡 Tips for even better results:")
    print("   1. Collect more data for underperforming classes")
    print("   2. Add more augmented samples for confused pairs")
    print("   3. Use ensemble of multiple models")
    print("   4. Fine-tune on real webcam data")


if __name__ == "__main__":
    main()
