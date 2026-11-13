"""
Model Evaluation and Metrics Module
Computes Top-1, Top-5 accuracy, per-class Precision/Recall/F1, Confusion Matrix,
and inference latency benchmarks for the ISL model.
"""

import os
import time
import json
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf
from train import load_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def evaluate_model(model_path: str, data_dir: str, classes_path: str, output_dir: str = "docs"):
    """Runs rigorous evaluation on the specified test set."""
    os.makedirs(output_dir, exist_ok=True)

    with open(classes_path, "r") as f:
        meta = json.load(f)
    classes = meta["classes"]

    if not os.path.exists(model_path):
        logger.error(f"Model file {model_path} does not exist.")
        return

    logger.info(f"Loading model from {model_path}...")
    model = tf.keras.models.load_model(model_path)

    logger.info(f"Loading evaluation data from {data_dir}...")
    X, y_true, _ = load_dataset(data_dir, classes_path)

    logger.info(f"Evaluating {len(X)} sequences...")

    # Benchmark Latency
    latencies = []
    # Warmup
    _ = model.predict(X[:1], verbose=0)

    for i in range(min(50, len(X))):
        start = time.perf_counter()
        _ = model.predict(X[i:i+1], verbose=0)
        latencies.append((time.perf_counter() - start) * 1000.0)

    mean_latency = np.mean(latencies)
    p95_latency = np.percentile(latencies, 95)
    logger.info(f"Inference Latency: Mean = {mean_latency:.2f} ms, 95th Percentile = {p95_latency:.2f} ms")

    # Full predictions
    probs = model.predict(X, batch_size=32, verbose=0)
    y_pred = np.argmax(probs, axis=1)

    # Top-1 Accuracy
    top1_acc = np.mean(y_pred == y_true) * 100.0

    # Top-5 Accuracy
    top5_correct = 0
    for idx, true_cls in enumerate(y_true):
        top5_preds = np.argsort(probs[idx])[-5:]
        if true_cls in top5_preds:
            top5_correct += 1
    top5_acc = (top5_correct / len(y_true)) * 100.0

    logger.info("==========================================")
    logger.info(f"Top-1 Accuracy : {top1_acc:.2f}%")
    logger.info(f"Top-5 Accuracy : {top5_acc:.2f}%")
    logger.info("==========================================")

    # Classification Report
    unique_present_classes = sorted(list(set(y_true) | set(y_pred)))
    target_names = [classes[i] for i in unique_present_classes]
    report = classification_report(y_true, y_pred, labels=unique_present_classes, target_names=target_names, zero_division=0)
    logger.info("\n" + report)

    # Save Confusion Matrix Plot
    cm = confusion_matrix(y_true, y_pred, labels=unique_present_classes)
    plt.figure(figsize=(12, 10))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title("ISL Model Confusion Matrix", fontsize=14)
    plt.colorbar()
    tick_marks = np.arange(len(target_names))
    plt.xticks(tick_marks, target_names, rotation=90, fontsize=8)
    plt.yticks(tick_marks, target_names, fontsize=8)
    plt.ylabel("True Class", fontsize=11)
    plt.xlabel("Predicted Class", fontsize=11)
    plt.tight_layout()

    cm_path = os.path.join(output_dir, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=200)
    plt.close()
    logger.info(f"Saved confusion matrix plot to {cm_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate ISL model")
    parser.add_argument("--model", type=str, default="isl_model.keras", help="Path to trained model")
    parser.add_argument("--data", type=str, default="data/processed", help="Path to processed sequences")
    parser.add_argument("--classes", type=str, default="data/classes.json", help="Path to classes.json")
    parser.add_argument("--output", type=str, default="docs", help="Directory for report outputs")
    args = parser.parse_args()

    evaluate_model(args.model, args.data, args.classes, output_dir=args.output)
